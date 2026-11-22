#!/usr/bin/env python3
"""
Step 4: Cinema-grade video assembly driven dynamically by timeline.json & shot_layout.py.
Per-act color grading (cold digital vs warm Kodak film), organic film grain,
supersampled Ken Burns micro-motion, bottom gradient scrim, ASS cinema typography,
and high-bitrate H.264 mastering.
"""
import concurrent.futures
import json
import os
import subprocess
import sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shot_layout import compute_shot_layout

WORK_DIR = "/tmp/zeitgeist_work"
CLIP_DIR = f"{WORK_DIR}/graded_clips"
OUT_DIR = "/agent/repos/Zeitgeist/output"
os.makedirs(CLIP_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.realpath("/opt/cursor/artifacts"), exist_ok=True)

FPS = 30
W, H = 1920, 1080


def grade_filter(mode, n_frames, zoom_dir="in"):
    nf = max(1, n_frames)
    if mode == "ui_cold":
        return f"fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1"
    if mode == "ui_warm":
        return f"fps={FPS},scale={W}:{H}:flags=lanczos,noise=alls=4:allf=t+u,setsar=1"

    if zoom_dir == "none":
        geo = f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
    else:
        z_expr = f"1+0.045*min(in/{nf},1)" if zoom_dir == "in" else f"1.045-0.045*min(in/{nf},1)"
        geo = (
            f"fps={FPS},scale=2560:1440:force_original_aspect_ratio=increase,crop=2560:1440,"
            f"zoompan=z='{z_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},setsar=1"
        )

    if mode == "cold":
        color = (
            "eq=contrast=1.08:brightness=-0.02:saturation=0.72,"
            "colorbalance=rs=-0.05:gs=-0.01:bs=0.07:rm=-0.04:gm=0.0:bm=0.06:rh=-0.03:gh=0.01:bh=0.06,"
            "vignette=PI/4.8"
        )
    elif mode == "warm":
        color = (
            "eq=contrast=1.06:brightness=-0.01:saturation=1.08,"
            "colorbalance=rs=0.04:gs=0.01:bs=-0.04:rm=0.06:gm=0.02:bm=-0.05:rh=0.08:gh=0.03:bh=-0.04,"
            "unsharp=3:3:0.35:3:3:0.0,"
            "noise=alls=6:allf=t+u,"
            "vignette=PI/4.2"
        )
    else:
        color = "null"
    return f"{geo},{color}"


def build_shot(args):
    idx, src, ss, n_frames, mode, zoom_dir, fade_in, fade_out, slow_factor = args
    dur = n_frames / FPS
    out_mp4 = f"{CLIP_DIR}/shot_{idx:02d}.mp4"
    if src == "BLACK":
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={FPS}:d={dur:.4f}",
            "-frames:v", str(n_frames),
            "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p",
            "-video_track_timescale", "15360",
            out_mp4
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return idx, out_mp4

    vf = grade_filter(mode, n_frames, zoom_dir=zoom_dir)
    if slow_factor != 1.0:
        vf = f"setpts={slow_factor:.4f}*PTS," + vf
    if fade_in > 0:
        vf += f",fade=t=in:st=0:d={fade_in:.3f}"
    if fade_out > 0:
        vf += f",fade=t=out:st={max(0, dur - fade_out):.3f}:d={fade_out:.3f}"

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-ss", f"{ss:.3f}", "-i", src,
        "-vf", vf,
        "-frames:v", str(n_frames),
        "-an",
        "-c:v", "libx264", "-preset", "fast", "-crf", "16",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-video_track_timescale", "15360",
        out_mp4
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return idx, out_mp4


def main():
    tl = json.load(open(f"{WORK_DIR}/timeline.json"))
    shots, by_tag = compute_shot_layout(tl)
    total_dur = tl["total_duration"]
    finale_start = by_tag["a5_finale_card"][0]

    raw_video = f"{WORK_DIR}/video_nosubs.mp4"
    if "--remux-only" not in sys.argv or not os.path.exists(raw_video):
        print(f"Building {len(shots)} graded cinema shots (total {total_dur:.2f}s)...")
        jobs = []
        for i, (s, e, src, ss, mode, zdir, fi, fo, sf, tag) in enumerate(shots):
            f_start = int(round(s * FPS))
            f_end = int(round(e * FPS))
            n_frames = max(1, f_end - f_start)
            jobs.append((i, src, ss, n_frames, mode, zdir, fi, fo, sf))

        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            for idx, out_clip in ex.map(build_shot, jobs):
                results[idx] = out_clip
                s, e, src, _, mode, *_, tag = shots[idx]
                print(f"  [{idx:02d}] {s:6.2f} -> {e:6.2f} ({e-s:5.2f}s) | {mode:7s} | {tag}")

        concat_txt = f"{WORK_DIR}/concat.txt"
        with open(concat_txt, "w") as f:
            f.write("\n".join(f"file '{results[i]}'" for i in range(len(shots))) + "\n")

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
            "-c", "copy", raw_video
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print("Reusing pre-graded video_nosubs.mp4 (--remux-only)...")

    final_mp4 = f"{OUT_DIR}/taste_to_touch_final.mp4"
    ass_path = f"{WORK_DIR}/subs/subtitles.ass"
    audio_wav = f"{WORK_DIR}/audio/final_audio_master.wav"
    scrim_png = f"{WORK_DIR}/bottom_scrim.png"

    arr = np.zeros((H, W, 4), dtype=np.uint8)
    y_start = int(H * 0.78)
    ramp = np.linspace(0.0, 1.0, H - y_start) ** 1.6
    arr[y_start:, :, 3] = (ramp * 132).astype(np.uint8)[:, None]
    Image.fromarray(arr, "RGBA").save(scrim_png)

    print("Rendering final cinema master with subtle scrim, ASS typography & cloned narration audio...")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", raw_video,
        "-i", scrim_png,
        "-i", audio_wav,
        "-filter_complex", f"[0:v][1:v]overlay=0:0:enable='lt(t,{finale_start:.2f})',ass={ass_path}[vout]",
        "-map", "[vout]", "-map", "2:a:0",
        "-c:v", "libx264", "-preset", "medium", "-crf", "21",
        "-maxrate", "3400k", "-bufsize", "6800k",
        "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
        "-movflags", "+faststart",
        "-shortest",
        final_mp4
    ], check=True)

    art_dir = os.path.realpath("/opt/cursor/artifacts")
    os.makedirs(art_dir, exist_ok=True)
    subprocess.run(["cp", final_mp4, os.path.join(art_dir, "taste_to_touch_final.mp4")], check=True)
    sz = os.path.getsize(final_mp4) / (1024 * 1024)
    print(f"DONE! Final master: {final_mp4} ({sz:.2f} MB)")


if __name__ == "__main__":
    main()
