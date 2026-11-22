#!/usr/bin/env python3
"""
Step 3: Cinema-grade multi-track sound design & mixing — dynamically locked to
timeline.json and shot_layout.py so every UI click, wine pour, J-Cut wood carve,
watch escapement, clay wheel, brush stroke, Delete + mechanical keystrokes, and
Bach Solo Cello Sarabande cadence align to the exact millisecond.
"""
import json
import os
import subprocess
import sys
import numpy as np
import soundfile as sf
from scipy.signal import butter, filtfilt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shot_layout import compute_shot_layout

WORK_DIR = "/tmp/zeitgeist_work"
RAW_SFX = f"{WORK_DIR}/raw/sfx"
RAW_MUS = f"{WORK_DIR}/raw/music"
SR = 48000


def load_stereo(path, target_sr=SR):
    tmp = "/tmp/zeitgeist_work/audio/_dec_tmp.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", path, "-ar", str(target_sr), "-ac", "2", tmp],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    data, sr = sf.read(tmp, dtype="float32")
    if data.ndim == 1:
        data = np.stack([data, data], axis=1)
    return data


def bandpass(sig, lo, hi, sr=SR, order=3):
    b, a = butter(order, [lo / (sr / 2), hi / (sr / 2)], btype="band")
    return filtfilt(b, a, sig, axis=0).astype(np.float32)


def lowpass(sig, cutoff, sr=SR, order=3):
    b, a = butter(order, cutoff / (sr / 2), btype="low")
    return filtfilt(b, a, sig, axis=0).astype(np.float32)


def highpass(sig, cutoff, sr=SR, order=2):
    b, a = butter(order, cutoff / (sr / 2), btype="high")
    return filtfilt(b, a, sig, axis=0).astype(np.float32)


def place(buf, clip, start_s, gain=1.0, fade_in=0.01, fade_out=0.02, max_dur=None):
    if max_dur is not None:
        clip = clip[:int(round(max_dur * SR))].copy()
    else:
        clip = clip.copy()
    n = len(clip)
    if n == 0:
        return
    fi = min(int(round(fade_in * SR)), n // 2)
    fo = min(int(round(fade_out * SR)), n // 2)
    if fi > 1:
        clip[:fi] *= np.linspace(0, 1, fi, dtype=np.float32)[:, None]
    if fo > 1:
        clip[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)[:, None]
    s = int(round(start_s * SR))
    e = s + n
    if s >= len(buf) or e <= 0:
        return
    cs = max(0, -s)
    bs = max(0, s)
    be = min(len(buf), e)
    ce = cs + (be - bs)
    buf[bs:be] += clip[cs:ce] * gain


def normalize_rms(sig, target=0.12):
    rms = np.sqrt(np.mean(sig ** 2) + 1e-12)
    return sig * (target / rms)


def synth_watch_escapement(dur_s):
    n = int(round(max(0.2, dur_s) * SR))
    out = np.zeros((n, 2), dtype=np.float32)
    rng = np.random.default_rng(42)
    dt = 0.25
    t = 0.08
    idx = 0
    while t < dur_s - 0.05:
        pos = int(round(t * SR))
        tick_len = int(0.018 * SR)
        tt = np.arange(tick_len, dtype=np.float32) / SR
        env = np.exp(-tt * 280.0)
        freq = 5100.0 if (idx % 2 == 0) else 5650.0
        tone = (
            0.55 * np.sin(2 * np.pi * freq * tt)
            + 0.30 * np.sin(2 * np.pi * (freq * 1.62) * tt)
            + 0.35 * rng.normal(0, 1, tick_len).astype(np.float32)
        ) * env
        amp = 0.22 if (idx % 2 == 0) else 0.17
        end = min(n, pos + tick_len)
        seg = tone[:end - pos] * amp
        out[pos:end, 0] += seg * 0.95
        out[pos:end, 1] += seg * 1.05
        t += dt + (0.002 if idx % 2 == 0 else -0.002)
        idx += 1
    return highpass(out, 1800)


def synth_clay_friction(dur_s):
    n = int(round(max(0.2, dur_s) * SR))
    rng = np.random.default_rng(108)
    tt = np.arange(n, dtype=np.float32) / SR
    noise = rng.normal(0, 1, (n, 2)).astype(np.float32)
    wet = bandpass(noise, 340, 1650, order=3)
    mod = 0.72 + 0.28 * np.sin(2 * np.pi * 1.45 * tt + 0.4)
    wheel = 0.05 * np.sin(2 * np.pi * 114.0 * tt) * (0.85 + 0.15 * np.sin(2 * np.pi * 1.45 * tt))
    out = wet * (mod[:, None] * 0.11) + wheel[:, None]
    return lowpass(out, 2400)


def synth_hand_sanding(dur_s):
    n = int(round(max(0.2, dur_s) * SR))
    rng = np.random.default_rng(209)
    tt = np.arange(n, dtype=np.float32) / SR
    noise = rng.normal(0, 1, (n, 2)).astype(np.float32)
    grain = bandpass(noise, 650, 3800, order=3)
    stroke = np.maximum(0.0, np.sin(2 * np.pi * 0.68 * tt)) ** 1.6
    stroke2 = np.maximum(0.0, -np.sin(2 * np.pi * 0.68 * tt)) ** 1.8 * 0.75
    env = 0.10 + 0.90 * (stroke + stroke2)
    return grain * (env[:, None] * 0.14)


def synth_tape_warmth(dur_s):
    n = int(round(max(0.2, dur_s) * SR))
    rng = np.random.default_rng(777)
    w = rng.normal(0, 1, (n, 2)).astype(np.float32)
    return bandpass(w, 180, 5200, order=2) * 0.0045


def synth_cold_shimmer(dur_s):
    n = int(round(max(0.2, dur_s) * SR))
    tt = np.arange(n, dtype=np.float32) / SR
    lfo = 0.8 + 0.2 * np.sin(2 * np.pi * 0.08 * tt)
    l = (
        0.45 * np.sin(2 * np.pi * 73.42 * tt)
        + 0.30 * np.sin(2 * np.pi * 110.00 * tt + 0.3)
        + 0.16 * np.sin(2 * np.pi * 164.81 * tt + 0.7)
        + 0.07 * np.sin(2 * np.pi * 329.63 * tt) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * tt))
    ) * lfo
    r = (
        0.45 * np.sin(2 * np.pi * 73.50 * tt)
        + 0.30 * np.sin(2 * np.pi * 110.12 * tt + 0.9)
        + 0.16 * np.sin(2 * np.pi * 164.95 * tt + 1.1)
        + 0.07 * np.sin(2 * np.pi * 329.85 * tt) * (0.5 + 0.5 * np.cos(2 * np.pi * 0.11 * tt))
    ) * lfo
    return np.stack([l, r], axis=1).astype(np.float32) * 0.065


def compute_ducking_curve(voice_stereo, duck_db=-6.8):
    mono = np.mean(np.abs(voice_stereo), axis=1)
    win = int(0.06 * SR)
    env = np.convolve(mono, np.ones(win, dtype=np.float32) / win, mode="same")
    active = np.clip((env - 0.012) / 0.035, 0.0, 1.0)
    smooth_win = int(0.28 * SR)
    sk = np.hanning(smooth_win).astype(np.float32)
    sk /= sk.sum()
    active_smooth = np.convolve(active, sk, mode="same")
    duck_lin = 10 ** (duck_db / 20.0)
    return (1.0 - active_smooth * (1.0 - duck_lin))[:, None].astype(np.float32)


def main():
    tl = json.load(open(f"{WORK_DIR}/timeline.json"))
    ui_ev = json.load(open(f"{WORK_DIR}/ui_events.json"))
    _, by_tag = compute_shot_layout(tl)

    voice = load_stereo(f"{WORK_DIR}/audio/narration_master.wav")
    total_samples = len(voice)
    total_dur = total_samples / SR
    print(f"Mixing dynamic soundscape for {total_dur:.2f}s ({total_samples} samples)...")

    acts = tl["acts"]
    cliff_start = acts["cliff"]["start"]
    cliff_end = acts["cliff"]["end"]
    jcut_start = acts["cliff"]["jcut_audio_start"]
    act3_end = acts["3"]["end"]

    bed_bus = np.zeros((total_samples, 2), dtype=np.float32)
    sfx_bus = np.zeros((total_samples, 2), dtype=np.float32)

    sfx_click = normalize_rms(load_stereo(f"{RAW_SFX}/mouse_click.mp3"), 0.18)
    sfx_select = normalize_rms(load_stereo(f"{RAW_SFX}/ui_select.mp3"), 0.15)
    sfx_whoosh = normalize_rms(load_stereo(f"{RAW_SFX}/whoosh_fast.mp3"), 0.12)
    sfx_pour = normalize_rms(load_stereo(f"{RAW_SFX}/water_pour.mp3"), 0.10)
    sfx_wood = normalize_rms(load_stereo(f"{RAW_SFX}/wood_saw.mp3"), 0.16)
    sfx_paper = normalize_rms(load_stereo(f"{RAW_SFX}/paper_slide.mp3"), 0.14)
    sfx_paper2 = normalize_rms(load_stereo(f"{RAW_SFX}/paper_wrinkle.mp3"), 0.12)
    sfx_kb_single = normalize_rms(load_stereo(f"{RAW_SFX}/kb_single.mp3"), 0.15)
    sfx_kb_slow = normalize_rms(load_stereo(f"{RAW_SFX}/kb_slow.mp3"), 0.14)
    sfx_shutter = normalize_rms(load_stereo(f"{RAW_SFX}/camera_shutter.mp3"), 0.15)
    sfx_drone = normalize_rms(load_stereo(f"{RAW_SFX}/drone_low.mp3"), 0.065)

    # --- ACT 1 & ACT 2 ---
    place(sfx_bus, sfx_select, 0.10, gain=0.85, fade_in=0.002, fade_out=0.03, max_dur=0.45)
    for tag in ["a1_flash1", "a1_flash2", "a1_taste_title", "a1_quote_feed"]:
        t_cut = by_tag[tag][0]
        place(sfx_bus, sfx_whoosh, max(0.0, t_cut - 0.08), gain=0.32, fade_in=0.02, fade_out=0.08, max_dur=0.45)

    cold_dur = cliff_start - 0.30
    drone_need = int(round(cold_dur * SR))
    if len(sfx_drone) < drone_need:
        reps = int(np.ceil(drone_need / len(sfx_drone)))
        sfx_drone = np.tile(sfx_drone, (reps, 1))
    drone_seg = lowpass(sfx_drone[:drone_need], 900)
    shimmer = synth_cold_shimmer(cold_dur)
    cold_bed = drone_seg * 0.72 + shimmer * 0.85
    place(bed_bus, cold_bed, 0.30, gain=0.85, fade_in=1.2, fade_out=0.008)

    wine_lp = lowpass(sfx_pour, 2200)
    place(sfx_bus, wine_lp, by_tag["a2_wine1"][0] + 0.25, gain=0.42, fade_in=0.4, fade_out=0.8, max_dur=4.5)
    place(sfx_bus, wine_lp, by_tag["a2_wine2"][0] + 0.15, gain=0.35, fade_in=0.5, fade_out=0.8, max_dur=4.2)

    regen_s, regen_e = by_tag["a2_regen"]
    for ct in ui_ev["act2_regenerate_clicks"]:
        if regen_s + ct < regen_e - 0.1:
            place(sfx_bus, sfx_click, regen_s + ct, gain=0.88, fade_in=0.002, fade_out=0.02, max_dur=0.30)

    grid_s, grid_e = by_tag["a2_grid"]
    for dt_tick in [0.0, 2.2, 4.2, 6.0, 6.55, 7.10, 7.65]:
        if grid_s + dt_tick < grid_e - 0.1:
            place(sfx_bus, sfx_select, grid_s + dt_tick, gain=0.28, fade_in=0.003, fade_out=0.02, max_dur=0.22)

    # --- CLIFF DEAD SILENCE ---
    z0 = int(round(cliff_start * SR))
    z1 = int(round(jcut_start * SR))
    bed_bus[z0:z1] = 0.0
    sfx_bus[z0:z1] = 0.0

    # --- ACT 3: PURE ASMR PHYSICAL FRICTION (NO MUSIC) ---
    wood_warm = bandpass(sfx_wood, 180, 4800, order=2)
    wc_s, wc_e = by_tag["a3_wood_chisel"]
    place(sfx_bus, wood_warm, jcut_start, gain=1.05, fade_in=0.06, fade_out=0.35, max_dur=3.8)
    if wc_e - jcut_start > 3.6:
        place(sfx_bus, wood_warm, jcut_start + 3.4, gain=0.65, fade_in=0.25, fade_out=0.55, max_dur=max(0.5, wc_e - (jcut_start + 3.4)))

    for tag in ["a3_clock_mech", "a3_clock_gears"]:
        s, e = by_tag[tag]
        place(sfx_bus, synth_watch_escapement(e - s), s, gain=0.70, fade_in=0.35, fade_out=0.45)

    for tag in ["a3_pottery_wheel", "a3_pottery_model", "a3_pottery_tool"]:
        s, e = by_tag[tag]
        place(bed_bus, synth_clay_friction(e - s), s, gain=0.90, fade_in=0.30, fade_out=0.40)

    carve_s, carve_e = by_tag["a3_wood_carve"]
    place(sfx_bus, wood_warm, carve_s + 0.15, gain=0.72, fade_in=0.20, fade_out=0.45, max_dur=max(0.5, carve_e - carve_s))
    det_s, det_e = by_tag["a3_wood_detail"]
    place(sfx_bus, wood_warm, det_s, gain=0.62, fade_in=0.20, fade_out=0.40, max_dur=max(0.5, det_e - det_s))

    br_s, br_e = by_tag["a3_brush_hand"]
    place(sfx_bus, lowpass(sfx_paper, 3600), br_s + 0.05, gain=0.85, fade_in=0.05, fade_out=0.15)
    place(sfx_bus, lowpass(sfx_paper2, 3200), br_s + 0.45, gain=0.72, fade_in=0.12, fade_out=0.30, max_dur=max(0.5, br_e - br_s - 0.45))

    sand_s, sand_e = by_tag["a3_wood_sand"]
    place(bed_bus, synth_hand_sanding(sand_e - sand_s), sand_s, gain=0.85, fade_in=0.30, fade_out=0.40)

    dough_s, dough_e = by_tag["a3_dough_form"]
    place(bed_bus, lowpass(synth_hand_sanding(dough_e - dough_s), 1400), dough_s, gain=0.55, fade_in=0.30, fade_out=0.60)

    place(bed_bus, synth_tape_warmth(act3_end - cliff_end), cliff_end, gain=0.60, fade_in=0.5, fade_out=0.8)

    # --- ACT 4 & FINALE: BACH SOLO CELLO SARABANDE + WARM TAPE + SYNCED KEYSTROKES ---
    cello = load_stereo(f"{RAW_MUS}/JOHN_MICHEL_CELLO-J_S_BACH_CELLO_SUITE_1_in_G_Sarabande.ogg")
    c_abs = np.max(np.abs(cello), axis=1)
    nz = np.where(c_abs > 0.002)[0]
    cello_end_s = (int(nz[-1]) if len(nz) else len(cello)) / SR

    cello_start_in_film = act3_end + 0.45
    cello_film_dur = (total_dur - 0.45) - cello_start_in_film
    cello_offset_s = max(0.0, cello_end_s - cello_film_dur)
    c0 = int(round(cello_offset_s * SR))
    c1 = min(len(cello), c0 + int(round(cello_film_dur * SR)))
    cello_clip = normalize_rms(lowpass(cello[c0:c1].copy(), 6800, order=2), 0.078)
    place(bed_bus, cello_clip, cello_start_in_film, gain=1.0, fade_in=4.2, fade_out=1.8)
    place(bed_bus, synth_tape_warmth(total_dur - act3_end), act3_end, gain=0.85, fade_in=2.0, fade_out=2.2)

    ed_s, ed_e = by_tag["a4_editor"]
    key_tap = sfx_kb_single[:int(0.14 * SR)].copy()
    del_tap = lowpass(sfx_kb_slow[:int(0.22 * SR)], 3400)
    if ed_s + ui_ev["act4_delete_time"] < ed_e:
        place(sfx_bus, del_tap, ed_s + ui_ev["act4_delete_time"], gain=0.95, fade_in=0.002, fade_out=0.04)
    rng = np.random.default_rng(2026)
    for kt in ui_ev["act4_key_times"]:
        if ed_s + kt < ed_e - 0.1:
            place(sfx_bus, key_tap, ed_s + kt, gain=float(rng.uniform(0.55, 0.85)), fade_in=0.002, fade_out=0.03)

    vf_s, vf_e = by_tag["a4_viewfinder"]
    place(sfx_bus, lowpass(sfx_shutter, 5500), vf_s + (vf_e - vf_s) * 0.45, gain=0.60, fade_in=0.003, fade_out=0.05, max_dur=0.6)

    # --- SIDECHAIN DUCKING & MASTERING ---
    bed_duck = compute_ducking_curve(voice, duck_db=-6.8)
    sfx_duck = compute_ducking_curve(voice, duck_db=-3.2)
    mix = voice * 1.0 + bed_bus * bed_duck + sfx_bus * sfx_duck

    peak = np.max(np.abs(mix))
    if peak > 0.94:
        mix = mix * (0.94 / peak)

    pre_wav = f"{WORK_DIR}/audio/mix_premaster.wav"
    master_wav = f"{WORK_DIR}/audio/final_audio_master.wav"
    sf.write(pre_wav, mix, SR)

    subprocess.run([
        "ffmpeg", "-y", "-i", pre_wav,
        "-af", "loudnorm=I=-14.5:TP=-1.0:LRA=11",
        "-ar", str(SR), "-ac", "2", master_wav
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Wrote final mastered audio:", master_wav)


if __name__ == "__main__":
    main()
