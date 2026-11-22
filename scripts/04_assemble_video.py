#!/usr/bin/env python3
"""
Step 4: Cinema-grade video assembly, per-act color grading (cold digital vs warm Kodak film),
organic film grain, slow Ken Burns motion, hard cuts / dissolves / J-Cut cliff,
ASS cinema subtitle rendering, and high-bitrate H.264 mastering.
"""
import concurrent.futures
import json
import os
import subprocess

WORK_DIR = "/tmp/zeitgeist_work"
RAW_VID = f"{WORK_DIR}/raw/videos"
UI_DIR = f"{WORK_DIR}/ui_renders"
CLIP_DIR = f"{WORK_DIR}/graded_clips"
OUT_DIR = "/agent/repos/Zeitgeist/output"
import sys
os.makedirs(CLIP_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.realpath("/opt/cursor/artifacts"), exist_ok=True)

FPS = 30
W, H = 1920, 1080


def grade_filter(mode, n_frames, zoom_dir="in"):
    """
    Build per-act cinema FFmpeg video filter chain:
    - 'black': pure pitch black
    - 'cold': Act 1-2 Silicon Valley / clinical cool cyan-slate grade, sharp, frictionless
    - 'warm': Act 3-5 Kodak warm amber-gold film grade + organic film grain + soft vignette
    - 'ui_cold' / 'ui_warm': clean custom 1080p UI renders (light grain on warm UI only)
    """
    nf = max(1, n_frames)
    if mode == "ui_cold":
        return f"fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1"
    if mode == "ui_warm":
        return f"fps={FPS},scale={W}:{H}:flags=lanczos,noise=alls=4:allf=t+u,setsar=1"

    if zoom_dir == "none":
        geo = f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
    else:
        # Supersampled 2560x1440 -> 1920x1080 subpixel zoompan: silky smooth, zero micro-jitter
        if zoom_dir == "in":
            z_expr = f"1+0.045*min(in/{nf},1)"
        else:
            z_expr = f"1.045-0.045*min(in/{nf},1)"
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
    total_dur = tl["total_duration"]
    acts = tl["acts"]

    # Master Shot List — every boundary sums continuously to exact total_duration!
    # Tuple: (start_s, end_s, source_path, in_ss, grade_mode, zoom_dir, fade_in, fade_out, slow_factor)
    shots = [
        # --- ACT 1: 平滑的狂欢 (0.00 -> 24.885) ---
        (0.000,   0.550, "BLACK", 0.0, "black", "none", 0.0, 0.0, 1.0),
        (0.550,   1.350, f"{RAW_VID}/a1_podcast2_2948.mp4", 1.5, "cold", "none", 0.0, 0.0, 1.0),
        (1.350,   2.150, f"{RAW_VID}/a1_stage_13222.mp4", 2.0, "cold", "none", 0.0, 0.0, 1.0),
        (2.150,   4.650, f"{UI_DIR}/ui_act1_taste_wall.mp4", 0.0, "ui_cold", "none", 0.0, 0.0, 1.0),
        (4.650,   7.950, f"{UI_DIR}/ui_act1_taste_wall.mp4", 2.8, "ui_cold", "none", 0.0, 0.0, 1.0),
        (7.950,  10.650, f"{RAW_VID}/a1_podcast3_2955.mp4", 2.0, "cold", "in", 0.0, 0.0, 1.0),
        (10.650, 12.950, f"{RAW_VID}/a1_min_room_3110.mp4", 1.5, "cold", "in", 0.0, 0.0, 1.0),
        (12.950, 15.250, f"{RAW_VID}/a1_min_cafe_4385.mp4", 2.0, "cold", "none", 0.0, 0.0, 1.0),
        (15.250, 17.650, f"{RAW_VID}/a1_coffee_3574.mp4", 1.0, "cold", "in", 0.0, 0.0, 1.0),
        (17.650, 24.885, f"{RAW_VID}/a1_cgi_sunset_33919.mp4", 1.0, "cold", "in", 0.25, 0.45, 1.25),

        # --- ACT 2: 舌头的逻辑 (24.885 -> 75.451) ---
        (24.885, 31.480, f"{RAW_VID}/a2_wine_black1_52407.mp4", 2.0, "cold", "in", 0.45, 0.0, 1.25),
        (31.480, 37.300, f"{RAW_VID}/a2_wine_black2_52406.mp4", 4.0, "cold", "in", 0.0, 0.0, 1.25),
        (37.300, 42.300, f"{RAW_VID}/a2_wine_white_52418.mp4", 3.0, "cold", "in", 0.0, 0.0, 1.25),
        (42.300, 47.960, f"{RAW_VID}/a2_scroll1_21364.mp4", 2.0, "cold", "in", 0.0, 0.0, 1.0),
        (47.960, 55.210, f"{UI_DIR}/ui_act2_regenerate.mp4", 0.0, "ui_cold", "none", 0.0, 0.0, 1.0),
        (55.210, 63.710, f"{UI_DIR}/ui_act2_pixel_grid.mp4", 0.0, "ui_cold", "none", 0.0, 0.0, 1.0),
        (63.710, 69.500, f"{RAW_VID}/a2_glasses_screen_14771.mp4", 0.0, "cold", "in", 0.0, 0.0, 1.15),
        (69.500, 75.451, f"{RAW_VID}/a2_museum2_46425.mp4", 2.0, "cold", "out", 0.0, 0.0, 1.0),

        # --- THE CLIFF: 1.50s DEAD BLACK (75.451 -> 76.951) ---
        (75.451, 76.951, "BLACK", 0.0, "black", "none", 0.0, 0.0, 1.0),

        # --- ACT 3: 进入阻力 / HANDWERKLICHKEIT (76.951 -> 134.050) ---
        (76.951, 83.850, f"{RAW_VID}/a3_wood_chisel_39500.mp4", 2.0, "warm", "in", 0.12, 0.0, 1.0),
        (83.850, 89.480, f"{RAW_VID}/a3_clock_mech_3651.mp4", 0.5, "warm", "in", 0.0, 0.0, 1.15),
        (89.480, 95.000, f"{RAW_VID}/a3_pottery_wheel_32085.mp4", 2.0, "warm", "in", 0.0, 0.0, 1.0),
        (95.000, 100.220, f"{RAW_VID}/a3_wood_carve_20438.mp4", 1.0, "warm", "in", 0.0, 0.0, 1.0),
        (100.220, 102.600, f"{RAW_VID}/a3_wood_detail_3815.mp4", 2.0, "warm", "in", 0.0, 0.0, 1.0),
        (102.600, 105.000, f"{RAW_VID}/a3_brush_hand_5197.mp4", 1.5, "warm", "in", 0.0, 0.0, 1.0),
        (105.000, 109.750, f"{RAW_VID}/a3_pottery_model_1973.mp4", 2.0, "warm", "in", 0.0, 0.0, 1.0),
        (109.750, 114.950, f"{RAW_VID}/a3_wood_sand2_20388.mp4", 2.0, "warm", "in", 0.0, 0.0, 1.0),
        (114.950, 120.100, f"{RAW_VID}/a3_pottery_tool_1979.mp4", 2.0, "warm", "in", 0.0, 0.0, 1.0),
        (120.100, 124.090, f"{RAW_VID}/a3_glass_craft_4175.mp4", 2.0, "warm", "in", 0.0, 0.0, 1.10),
        (124.090, 129.400, f"{RAW_VID}/a3_clock_gears_2561.mp4", 1.5, "warm", "in", 0.0, 0.0, 1.15),
        (129.400, 134.050, f"{RAW_VID}/a3_dough_form_42466.mp4", 0.5, "warm", "in", 0.0, 0.45, 1.15),

        # --- ACT 4: 数字时代的毛边 (134.050 -> 177.137) ---
        (134.050, 141.000, f"{RAW_VID}/a4_typing_laptop_1808.mp4", 1.0, "warm", "in", 0.45, 0.0, 1.0),
        (141.000, 145.350, f"{RAW_VID}/a3_dough_mix_42464.mp4", 1.0, "warm", "in", 0.0, 0.0, 1.0),
        (145.350, 152.800, f"{RAW_VID}/a4_typing_close_47321.mp4", 1.5, "warm", "in", 0.0, 0.25, 1.0),
        (152.800, 168.300, f"{UI_DIR}/ui_act4_rough_edge_editor.mp4", 0.0, "ui_warm", "none", 0.30, 0.30, 1.0),
        (168.300, 172.700, f"{RAW_VID}/a4_mixer_knobs_25242.mp4", 3.0, "warm", "in", 0.25, 0.0, 1.0),
        (172.700, 177.137, f"{RAW_VID}/a4_viewfinder_49652.mp4", 2.0, "warm", "in", 0.0, 0.35, 1.0),

        # --- ACT 5: 尾声 · 人类双手肖像蒙太奇 + WE TOUCH. (177.137 -> total_dur) ---
        (177.137, 180.900, f"{RAW_VID}/a5_elderly_hands_48789.mp4", 2.0, "warm", "in", 0.35, 0.25, 1.15),
        (180.900, 184.600, f"{RAW_VID}/a5_child_paint_15163.mp4", 3.0, "warm", "in", 0.25, 0.25, 1.15),
        (184.600, 187.700, f"{RAW_VID}/a5_hand_wheat_8864.mp4", 2.0, "warm", "in", 0.25, 0.25, 1.15),
        (187.700, 190.400, f"{RAW_VID}/a5_hand_leaves_2563.mp4", 4.0, "warm", "in", 0.25, 0.55, 1.15),
        (190.400, total_dur, f"{UI_DIR}/ui_finale_we_touch.mp4", 0.0, "ui_warm", "none", 0.30, 0.0, 1.0),
    ]

    raw_video = f"{WORK_DIR}/video_nosubs.mp4"
    if "--remux-only" not in sys.argv or not os.path.exists(raw_video):
        print(f"Building {len(shots)} graded cinema shots (total {total_dur:.2f}s)...")
        jobs = []
        for i, (s, e, src, ss, mode, zdir, fi, fo, sf) in enumerate(shots):
            f_start = int(round(s * FPS))
            f_end = int(round(e * FPS))
            n_frames = max(1, f_end - f_start)
            jobs.append((i, src, ss, n_frames, mode, zdir, fi, fo, sf))

        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            for idx, out_clip in ex.map(build_shot, jobs):
                results[idx] = out_clip
                s, e, src, _, mode, *_ = shots[idx]
                print(f"  [{idx:02d}] {s:6.2f} -> {e:6.2f} ({e-s:5.2f}s) | {mode:7s} | {os.path.basename(src)}")

        concat_lines = [f"file '{results[i]}'" for i in range(len(shots))]

        concat_txt = f"{WORK_DIR}/concat.txt"
        with open(concat_txt, "w") as f:
            f.write("\n".join(concat_lines) + "\n")

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
            "-c", "copy", raw_video
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print("Reusing pre-graded video_nosubs.mp4 (--remux-only)...")

    # Burn cinema bottom gradient scrim + ASS subtitles + mux mastered audio -> final release master!
    final_mp4 = f"{OUT_DIR}/taste_to_touch_final.mp4"
    ass_path = f"{WORK_DIR}/subs/subtitles.ass"
    audio_wav = f"{WORK_DIR}/audio/final_audio_master.wav"
    scrim_png = f"{WORK_DIR}/bottom_scrim.png"

    # Generate subtle cinema bottom gradient scrim (transparent top 78% -> soft 48% dark bottom veil)
    # Guarantees crisp subtitle legibility over sunlit shots without any visible hard box
    from PIL import Image
    import numpy as np
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    y_start = int(H * 0.78)
    ramp = np.linspace(0.0, 1.0, H - y_start) ** 1.6
    arr[y_start:, :, 3] = (ramp * 132).astype(np.uint8)[:, None]
    Image.fromarray(arr, "RGBA").save(scrim_png)

    print("Rendering final cinema master with subtle scrim, ASS typography & mastered stereo audio...")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", raw_video,
        "-i", scrim_png,
        "-i", audio_wav,
        "-filter_complex", f"[0:v][1:v]overlay=0:0:enable='lt(t,190.4)',ass={ass_path}[vout]",
        "-map", "[vout]", "-map", "2:a:0",
        "-c:v", "libx264", "-preset", "medium", "-crf", "21",
        "-maxrate", "3400k", "-bufsize", "6800k",
        "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
        "-movflags", "+faststart",
        "-shortest",
        final_mp4
    ], check=True)

    # Copy to /opt/cursor/artifacts for PR video preview too
    art_dir = os.path.realpath("/opt/cursor/artifacts")
    os.makedirs(art_dir, exist_ok=True)
    subprocess.run(["cp", final_mp4, os.path.join(art_dir, "taste_to_touch_final.mp4")], check=True)
    sz = os.path.getsize(final_mp4) / (1024 * 1024)
    print(f"DONE! Final master: {final_mp4} ({sz:.2f} MB)")


if __name__ == "__main__":
    main()
