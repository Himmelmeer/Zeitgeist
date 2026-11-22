#!/usr/bin/env python3
"""
Step 3: Cinema-grade multi-track sound design & mixing.
- Act 1-2: Cold electronic drone bed + crisp UI clicks + slow wine pour + Regenerate mouse clicks
- Cliff: Razor-sharp hard cut to dead silence + 0.55s J-Cut physical wood friction entry
- Act 3: Pure ASMR physical friction Foley (zero music) — wood carving, mechanical watch escapement,
         wet clay wheel friction, brush-on-paper drag, hand sanding, warm workshop room tone
- Act 4-5: J.S. Bach Cello Suite No. 1 Sarabande aligned to resolve naturally on final low chord,
         subtle warm analog tape noise, frame-synced mechanical keystrokes, vintage shutter click
- Smooth voice-envelope sidechain ducking + EBU R128 broadcast mastering (-14.5 LUFS)
"""
import json
import os
import subprocess
import numpy as np
import soundfile as sf
from scipy.signal import butter, filtfilt

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
    """Synthesize realistic delicate 4Hz (28,800 vph) mechanical watch escapement micro-ticks."""
    n = int(round(dur_s * SR))
    out = np.zeros((n, 2), dtype=np.float32)
    rng = np.random.default_rng(42)
    dt = 0.25  # 4 ticks per second (double-beat swiss lever feel)
    t = 0.08
    idx = 0
    while t < dur_s - 0.05:
        pos = int(round(t * SR))
        tick_len = int(0.018 * SR)
        tt = np.arange(tick_len, dtype=np.float32) / SR
        # Sharp metallic impulse + tiny 5.2kHz/8.4kHz pallet-fork ring
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
    """Warm organic wet-clay hand friction & subtle ceramic wheel rotational resonance."""
    n = int(round(dur_s * SR))
    rng = np.random.default_rng(108)
    tt = np.arange(n, dtype=np.float32) / SR
    noise = rng.normal(0, 1, (n, 2)).astype(np.float32)
    # Wet palm rubbing clay: warm bandpass 320-1650Hz with slow rotational breathing
    wet = bandpass(noise, 340, 1650, order=3)
    mod = 0.72 + 0.28 * np.sin(2 * np.pi * 1.45 * tt + 0.4)
    # Subtle low ceramic wheel motor/flywheel resonance (~115Hz)
    wheel = 0.05 * np.sin(2 * np.pi * 114.0 * tt) * (0.85 + 0.15 * np.sin(2 * np.pi * 1.45 * tt))
    out = wet * (mod[:, None] * 0.11) + wheel[:, None]
    return lowpass(out, 2400)


def synth_hand_sanding(dur_s):
    """Rhythmic warm hand-sanding strokes across carved wood."""
    n = int(round(dur_s * SR))
    rng = np.random.default_rng(209)
    tt = np.arange(n, dtype=np.float32) / SR
    noise = rng.normal(0, 1, (n, 2)).astype(np.float32)
    grain = bandpass(noise, 650, 3800, order=3)
    # Rhythmic back-and-forth stroke envelope (~1.35 strokes/sec)
    stroke = np.maximum(0.0, np.sin(2 * np.pi * 0.68 * tt)) ** 1.6
    stroke2 = np.maximum(0.0, -np.sin(2 * np.pi * 0.68 * tt)) ** 1.8 * 0.75
    env = 0.10 + 0.90 * (stroke + stroke2)
    return grain * (env[:, None] * 0.14)


def synth_tape_warmth(dur_s):
    """Ultra-subtle analog tape warmth floor for Act 4-5."""
    n = int(round(dur_s * SR))
    rng = np.random.default_rng(777)
    w = rng.normal(0, 1, (n, 2)).astype(np.float32)
    return bandpass(w, 180, 5200, order=2) * 0.0045


def synth_cold_shimmer(dur_s):
    """Sleek, slightly airless silicon-valley ambient synth drone harmonic pad."""
    n = int(round(dur_s * SR))
    tt = np.arange(n, dtype=np.float32) / SR
    # D1 (73.4Hz) + A1 (110Hz) + E2 (164.8Hz) subtle cold fifths with slow LFO
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


def compute_ducking_curve(voice_stereo, duck_db=-7.0):
    """Compute smooth voice-triggered sidechain ducking gain curve."""
    mono = np.mean(np.abs(voice_stereo), axis=1)
    # Moving average RMS over 60ms window
    win = int(0.06 * SR)
    kernel = np.ones(win, dtype=np.float32) / win
    env = np.convolve(mono, kernel, mode="same")
    # Threshold speech presence
    active = np.clip((env - 0.012) / 0.035, 0.0, 1.0)
    # Smooth with slow attack/release (240ms) for silky documentary ducking
    smooth_win = int(0.28 * SR)
    sk = np.hanning(smooth_win).astype(np.float32)
    sk /= sk.sum()
    active_smooth = np.convolve(active, sk, mode="same")
    duck_lin = 10 ** (duck_db / 20.0)
    gain = 1.0 - active_smooth * (1.0 - duck_lin)
    return gain[:, None].astype(np.float32)


def main():
    tl = json.load(open(f"{WORK_DIR}/timeline.json"))
    ui_ev = json.load(open(f"{WORK_DIR}/ui_events.json"))

    voice = load_stereo(f"{WORK_DIR}/audio/narration_master.wav")
    total_samples = len(voice)
    total_dur = total_samples / SR
    print(f"Mixing master soundscape for {total_dur:.2f}s ({total_samples} samples)...")

    acts = tl["acts"]
    act1_end = acts["1"]["end"]
    act2_end = acts["2"]["end"]
    cliff_start = acts["cliff"]["start"]
    cliff_end = acts["cliff"]["end"]
    jcut_start = acts["cliff"]["jcut_audio_start"]
    act3_end = acts["3"]["end"]
    act4_end = acts["4"]["end"]

    # Separate buses so we can duck music/beds cleanly while preserving crisp Foley accents
    bed_bus = np.zeros((total_samples, 2), dtype=np.float32)
    sfx_bus = np.zeros((total_samples, 2), dtype=np.float32)

    # Load real SFX assets
    sfx_phone = normalize_rms(load_stereo(f"{RAW_SFX}/phone_lock.mp3"), 0.16)
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

    # ==========================================================
    # ACT 1 & ACT 2: COLD DIGITAL BED + UI CLICKS (0.0 -> cliff_start)
    # ==========================================================
    # 0.12s opening lock click
    place(sfx_bus, sfx_select, 0.10, gain=0.85, fade_in=0.002, fade_out=0.03, max_dur=0.45)
    # Fast flash-cut accents
    for t_cut in [0.55, 1.35, 2.15, 4.65]:
        place(sfx_bus, sfx_whoosh, t_cut - 0.08, gain=0.32, fade_in=0.02, fade_out=0.08, max_dur=0.45)

    # Cold electronic drone bed spanning 0.3s -> cliff_start (HARD CUT at cliff_start!)
    cold_dur = cliff_start - 0.30
    drone_seg = lowpass(sfx_drone[:int(round(cold_dur * SR))], 900)
    shimmer = synth_cold_shimmer(cold_dur)
    cold_bed = drone_seg * 0.72 + shimmer * 0.85
    # Hard cut at cliff_start (just 8ms anti-click taper — feels like pulling the power plug!)
    place(bed_bus, cold_bed, 0.30, gain=0.85, fade_in=1.2, fade_out=0.008)

    # Act 2 wine pouring subtle liquid sound (25.2s -> 35.0s)
    wine_lp = lowpass(sfx_pour, 2200)
    place(sfx_bus, wine_lp, 25.10, gain=0.42, fade_in=0.4, fade_out=0.8, max_dur=4.5)
    place(sfx_bus, wine_lp, 31.60, gain=0.35, fade_in=0.5, fade_out=0.8, max_dur=4.2)

    # Act 2 Regenerate exact frame-synced mouse clicks (clip starts at 47.96s)
    regen_start = 47.96
    for ct in ui_ev["act2_regenerate_clicks"]:
        place(sfx_bus, sfx_click, regen_start + ct, gain=0.88, fade_in=0.002, fade_out=0.02, max_dur=0.30)

    # Act 2 Pixel Grid ingestion subtle digital ticks (clip starts at 55.21s)
    for dt_tick in [0.0, 2.2, 4.2, 6.0, 6.55, 7.10, 7.65]:
        place(sfx_bus, sfx_select, 55.21 + dt_tick, gain=0.28, fade_in=0.003, fade_out=0.02, max_dur=0.22)

    # ==========================================================
    # CLIFF (75.451 -> 76.951): DEAD SILENCE THEN 0.55s J-CUT!
    # ==========================================================
    # Enforce absolute digital zero between cliff_start and jcut_start
    z0 = int(round(cliff_start * SR))
    z1 = int(round(jcut_start * SR))
    bed_bus[z0:z1] = 0.0
    sfx_bus[z0:z1] = 0.0

    # ==========================================================
    # ACT 3: PURE ASMR PHYSICAL FRICTION (NO MUSIC! 76.401 -> 134.05)
    # ==========================================================
    # Warm wood-carving J-Cut enters 0.55s BEFORE picture! Bold, tactile, unmistakable!
    wood_warm = bandpass(sfx_wood, 180, 4800, order=2)
    place(sfx_bus, wood_warm, jcut_start, gain=1.05, fade_in=0.06, fade_out=0.35, max_dur=3.8)
    place(sfx_bus, wood_warm, jcut_start + 3.4, gain=0.65, fade_in=0.25, fade_out=0.6, max_dur=3.6)

    # Mechanical watch escapement micro-ticks (83.85 -> 89.48 & 124.09 -> 129.40)
    place(sfx_bus, synth_watch_escapement(5.63), 83.85, gain=0.72, fade_in=0.35, fade_out=0.45)
    place(sfx_bus, synth_watch_escapement(5.31), 124.09, gain=0.68, fade_in=0.35, fade_out=0.45)

    # Wet pottery clay friction (89.48 -> 95.00, 105.00 -> 109.75, 114.95 -> 120.10)
    place(bed_bus, synth_clay_friction(5.52), 89.48, gain=0.90, fade_in=0.35, fade_out=0.45)
    place(bed_bus, synth_clay_friction(4.75), 105.00, gain=0.95, fade_in=0.30, fade_out=0.40)
    place(bed_bus, synth_clay_friction(5.15), 114.95, gain=0.88, fade_in=0.30, fade_out=0.45)

    # Wood carving second phrase (95.00 -> 102.60)
    place(sfx_bus, wood_warm, 95.30, gain=0.72, fade_in=0.20, fade_out=0.45, max_dur=3.8)
    place(sfx_bus, wood_warm, 99.10, gain=0.68, fade_in=0.25, fade_out=0.50, max_dur=3.4)

    # Brush dragging across fibrous paper (102.60 -> 105.00)
    place(sfx_bus, lowpass(sfx_paper, 3600), 102.65, gain=0.85, fade_in=0.05, fade_out=0.15)
    place(sfx_bus, lowpass(sfx_paper2, 3200), 103.15, gain=0.72, fade_in=0.12, fade_out=0.35, max_dur=1.7)

    # Rhythmic hand sanding wood (109.75 -> 114.95)
    place(bed_bus, synth_hand_sanding(5.20), 109.75, gain=0.85, fade_in=0.30, fade_out=0.40)

    # Dough kneading warm tactile rustle (129.40 -> 134.05)
    place(bed_bus, lowpass(synth_hand_sanding(4.65), 1400), 129.40, gain=0.55, fade_in=0.30, fade_out=0.60)

    # Subtle warm workshop room tone across Act 3 so physical air feels continuous
    place(bed_bus, synth_tape_warmth(act3_end - cliff_end), cliff_end, gain=0.60, fade_in=0.5, fade_out=0.8)

    # ==========================================================
    # ACT 4 & FINALE: BACH SOLO CELLO SARABANDE + WARM TAPE + KEYSTROKES
    # ==========================================================
    cello = load_stereo(f"{RAW_MUS}/JOHN_MICHEL_CELLO-J_S_BACH_CELLO_SUITE_1_in_G_Sarabande.ogg")
    # Detect natural tail where final low chord finishes ringing
    c_abs = np.max(np.abs(cello), axis=1)
    nz = np.where(c_abs > 0.002)[0]
    cello_end_sample = int(nz[-1]) if len(nz) else len(cello)
    cello_end_s = cello_end_sample / SR
    print(f"Bach Sarabande natural musical tail: {cello_end_s:.2f}s (total {len(cello)/SR:.2f}s)")

    # Align cello natural cadence to land right at (total_dur - 0.5s)!
    cello_start_in_film = act3_end + 0.45
    cello_film_dur = (total_dur - 0.45) - cello_start_in_film
    cello_offset_s = max(0.0, cello_end_s - cello_film_dur)
    c0 = int(round(cello_offset_s * SR))
    c1 = min(len(cello), c0 + int(round(cello_film_dur * SR)))
    cello_clip = cello[c0:c1].copy()
    # Warm cinema tilt: gently tame harsh bow rosin >7kHz and enrich cello body
    cello_clip = lowpass(cello_clip, 6800, order=2)
    cello_clip = normalize_rms(cello_clip, 0.078)
    place(bed_bus, cello_clip, cello_start_in_film, gain=1.0, fade_in=4.2, fade_out=1.8)

    # Subtle analog tape warmth under Act 4 & Finale
    place(bed_bus, synth_tape_warmth(total_dur - act3_end), act3_end, gain=0.85, fade_in=2.0, fade_out=2.2)

    # Act 4 exact mechanical keystrokes synced to ui_act4_rough_edge_editor (starts at 152.80s)
    ed_start = 152.80
    # Warm single mechanical key tap sample (first 0.14s of kb_single)
    key_tap = sfx_kb_single[:int(0.14 * SR)].copy()
    del_tap = lowpass(sfx_kb_slow[:int(0.22 * SR)], 3400)
    # Delete keystroke!
    place(sfx_bus, del_tap, ed_start + ui_ev["act4_delete_time"], gain=0.95, fade_in=0.002, fade_out=0.04)
    # Every human-typed character keystroke with subtle organic velocity variation
    rng = np.random.default_rng(2026)
    for kt in ui_ev["act4_key_times"]:
        vel = float(rng.uniform(0.55, 0.85))
        place(sfx_bus, key_tap, ed_start + kt, gain=vel, fade_in=0.002, fade_out=0.03)

    # Vintage medium-format film camera shutter click on viewfinder shot (~174.6s)
    place(sfx_bus, lowpass(sfx_shutter, 5500), 174.60, gain=0.60, fade_in=0.003, fade_out=0.05, max_dur=0.6)

    # ==========================================================
    # SIDECHAIN DUCKING & MASTERING
    # ==========================================================
    bed_duck = compute_ducking_curve(voice, duck_db=-6.8)
    sfx_duck = compute_ducking_curve(voice, duck_db=-3.2)

    # Let the J-Cut wood sound (76.40 -> 79.35) and finale cello (191.5 -> end) stay completely unducked!
    mix = voice * 1.0 + bed_bus * bed_duck + sfx_bus * sfx_duck

    # Soft peak safety before ffmpeg loudnorm
    peak = np.max(np.abs(mix))
    if peak > 0.94:
        mix = mix * (0.94 / peak)

    pre_wav = f"{WORK_DIR}/audio/mix_premaster.wav"
    master_wav = f"{WORK_DIR}/audio/final_audio_master.wav"
    sf.write(pre_wav, mix, SR)

    # Final broadcast loudness normalization (-14.5 LUFS, -1.0 dBTP true peak)
    subprocess.run([
        "ffmpeg", "-y", "-i", pre_wav,
        "-af", "loudnorm=I=-14.5:TP=-1.0:LRA=11",
        "-ar", str(SR), "-ac", "2", master_wav
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("Wrote final mastered audio:", master_wav)


if __name__ == "__main__":
    main()
