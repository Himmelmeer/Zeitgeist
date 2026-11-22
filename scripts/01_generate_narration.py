#!/usr/bin/env python3
"""
Step 1: Zero-shot voice-cloned documentary narration using F5-TTS v1 Base
cloned from the creator's ElevenLabs IVC reference sample, with:
- Automatic Faster-Whisper back-transcription QA & seed retry per cue
- Broadcast studio vocal mastering chain (EQ, de-ess, warm compression, -16 LUFS)
- Exact timeline.json generation + Whisper-aligned cinema ASS subtitles
"""
import difflib
import json
import os
import re
import subprocess
import time
import numpy as np
import soundfile as sf
import torch
import torchaudio
from f5_tts.api import F5TTS
from faster_whisper import WhisperModel

# Soundfile-backed torchaudio.load override (avoids CUDA torchcodec on CPU VMs)
def _sf_load(path, *args, **kwargs):
    data, sr = sf.read(str(path), dtype="float32", always_2d=True)
    return torch.from_numpy(data.T.copy()), sr

torchaudio.load = _sf_load
torch.set_num_threads(4)

WORK_DIR = "/tmp/zeitgeist_work"
SEG_DIR = f"{WORK_DIR}/audio/segs_cloned"
os.makedirs(SEG_DIR, exist_ok=True)
os.makedirs(f"{WORK_DIR}/subs", exist_ok=True)

UPLOADED_MP3 = "/home/ubuntu/.cursor/projects/agent-repos-Zeitgeist/uploads/ElevenLabs__IVC-__1122_eleven_v4_stab0.4-style0.3_996c.mp3"
REF_WAV = f"{WORK_DIR}/audio/ref_clean6s.wav"
REF_TEXT = "我看完，发现一件挺有意思的事。公司赚了多少钱，做成了什么生意，一句没提。"
SR = 48000

# 18 natural spoken thought-group cues (optimal 16-38 char window for F5-TTS v1 cadence)
# (id, act, gen_text, subtitle_text, speed, pre_pause_s, post_pause_s)
CUES = [
    # --- ACT 1: 平滑的狂欢 (4.0s visual hook before narrator enters) ---
    ("a1_01", 1,
     "这两年，科技圈和设计界最常挂在嘴边的词，叫 Taste，品味。",
     "这两年，科技圈和设计界最常挂在嘴边的词，叫 Taste —— 品味。",
     0.95, 4.00, 0.55),
    ("a1_02", 1,
     "人们说，AI 已经接管了执行，未来人类唯一剩下的护城河，就是好品味。",
     "人们说，AI 已经接管了执行，未来人类唯一剩下的护城河，就是“好品味”。",
     0.95, 0.00, 0.70),
    ("a1_03", 1,
     "听起来很体面。可每次听到这个词，我心里总会冒出一种奇怪的违和感。",
     "听起来很体面。可每次听到这个词，我心里总会冒出一种奇怪的违和感。",
     0.92, 0.00, 2.35),

    # --- ACT 2: 舌头的逻辑 ---
    ("a2_01", 2,
     "看看这个词本身吧。Taste，味觉，属于舌头。它发生在一切已经完成之后。",
     "看看这个词本身吧。Taste，味觉，属于舌头。它发生在一切已经完成之后。",
     0.94, 1.80, 0.65),
    ("a2_02", 2,
     "菜端上来了，你尝一口，给出一个判决：喜欢，或者讨厌；高级，或者庸俗。",
     "菜端上来了，你尝一口，给出一个判决：喜欢，或者讨厌；高级，或者庸俗。",
     0.94, 0.00, 0.65),
    ("a2_03", 2,
     "如果不合胃口，吐掉就行。你的舌头，从来不需要去改造这道菜。",
     "如果不合胃口，吐掉就行。你的舌头，从来不需要去改造这道菜。",
     0.94, 0.00, 0.85),
    ("a2_04", 2,
     "品味，是一种站在安全距离之外的筛选。它依赖的，是见多识广的数据库。",
     "品味是一种站在安全距离之外的筛选。它依赖的，是见多识广的数据库。",
     0.94, 0.00, 0.85),
    ("a2_05", 2,
     "可问题是，今天，AI 已经吞下了全人类几千年的视觉、听觉和文本遗产。",
     "可问题是——今天，AI 已经吞下了全人类几千年的视觉、听觉和文本遗产。",
     0.95, 0.00, 0.60),
    ("a2_06", 2,
     "如果仅仅是选出最体面、最符合高级审美的那个选项，算法正在以惊人的速度追平我们。",
     "如果仅仅是“选出最体面、最符合高级审美的那个选项”，算法正在以惊人的速度追平我们。",
     0.95, 0.00, 0.80),
    ("a2_07", 2,
     "当每个人都在修炼好品味，世界反而变得越来越像。",
     "当每个人都在修炼“好品味”，世界反而变得越来越像。",
     0.90, 0.00, 1.35),

    # --- CLIFF (1.50s dead black) + ACT 3 (2.40s pure wood ASMR before voice) ---
    ("a3_01", 3,
     "如果让我换掉品味这个词，我选 Touch，手感。",
     "如果让我换掉“品味”这个词，我选 Touch —— 手感。",
     0.90, 3.90, 0.80),
    ("a3_02", 3,
     "德语里有一个更沉甸甸的词，叫 Handwerklichkeit，手作性。",
     "德语里有一个更沉甸甸的词，叫 Handwerklichkeit —— 手作性。",
     0.88, 0.00, 0.90),
    ("a3_03", 3,
     "舌头只负责消费结果，手，却必须伸进材料里。当你真正去触摸一样东西，世界是会推回来的。",
     "舌头只负责消费结果，手，却必须伸进材料里。当你真正去触摸一样东西，世界是会推回来的。",
     0.90, 0.00, 1.60),
    ("a3_04", 3,
     "木头有纹理的倔强，宣纸有吸墨的脾气，泥土有离心力的反抗。你施力，它抵抗；你微调，它变形。",
     "木头有纹理的倔强，宣纸有吸墨的脾气，泥土有离心力的反抗。你施力，它抵抗；你微调，它变形。",
     0.91, 0.00, 0.90),
    ("a3_05", 3,
     "就在这成百上千次的摩擦和拉锯里，发生了一件奇妙的事：你在打磨材料，材料也在反向塑形你的神经系统。",
     "就在这成百上千次的摩擦和拉锯里，发生了一件奇妙的事：你在打磨材料，材料也在反向塑形你的神经系统。",
     0.92, 0.00, 0.95),
    ("a3_06", 3,
     "中国人管这种状态叫，心手合一。那种长在肌肉记忆里的分寸感，靠看一万张参考图是学不会的。",
     "中国人管这种状态叫“心手合一”。那种长在肌肉记忆里的分寸感，靠看一万张参考图是学不会的。",
     0.90, 0.00, 0.65),
    ("a3_07", 3,
     "它只能从阻力里长出来。",
     "它只能从阻力里长出来。",
     0.86, 0.00, 2.20),

    # --- ACT 4: 数字时代的毛边 ---
    ("a4_01", 4,
     "有人会说，AI 时代，我们早就隔着屏幕干活了，哪来的手作？可手感，从来不只属于木匠和陶工。",
     "有人会说，AI 时代，我们早就隔着屏幕干活了，哪来的手作？可手感，从来不只属于木匠和陶工。",
     0.92, 1.50, 0.90),
    ("a4_02", 4,
     "当 AI 把从意图到结果的距离压缩为零，给我们端上一盘盘毫无瑕疵的平滑产物时，",
     "当 AI 把从“意图”到“结果”的距离压缩为零，给我们端上一盘盘毫无瑕疵的平滑产物时，",
     0.93, 0.00, 0.45),
    ("a4_03", 4,
     "真正的创作者依然能敏锐地察觉到：这里太滑了，那里太假了，这不像人说的话。",
     "真正的创作者依然能敏锐地察觉到：这里太滑了，那里太假了，这不像人说的话。",
     0.91, 0.00, 1.85),
    ("a4_04", 4,
     "于是你停下来，亲手把那一点犹豫、那一点停顿、那一点带着个人体温的毛边拉回来。",
     "于是你停下来，亲手把那一点犹豫、那一点停顿、那一点带着个人体温的“毛边”拉回来。",
     0.90, 0.00, 1.00),
    ("a4_05", 4,
     "在一个全面加速的时代，主动保留一点阻力，就是我们握紧方向盘的方式。",
     "在一个全面加速的时代，主动保留一点阻力，就是我们握紧方向盘的方式。",
     0.90, 0.00, 2.00),

    # --- ACT 5: 尾声宣言 ---
    ("a5_01", 5,
     "评论家谈品味，创造者练手感。别只满足于做一个挑剔的旁观者。",
     "评论家谈品味，创造者练手感。别只满足于做一个挑剔的旁观者。",
     0.88, 1.20, 1.15),
    ("a5_02", 5,
     "伸出手，去碰触阻力，去留下指纹。",
     "伸出手，去碰触阻力，去留下指纹。",
     0.86, 0.00, 1.70),
    ("a5_03", 5,
     "We touch.",
     "",
     0.82, 0.00, 8.20),
]


def norm_text(s):
    return re.sub(r"[\s，。、；：？！“”\"'—\-,.!?]+", "", s).lower()


def score_asr(target, rec):
    t = norm_text(target)
    r = norm_text(rec)
    if not t:
        return 1.0
    # Penalize obvious repetition if ASR is way longer than target
    len_ratio = len(r) / max(1, len(t))
    if len_ratio > 1.45 or len_ratio < 0.55:
        return 0.35
    return difflib.SequenceMatcher(None, t, r).ratio()


def prepare_reference():
    if not os.path.exists(REF_WAV):
        subprocess.run([
            "ffmpeg", "-y", "-ss", "8.05", "-t", "6.38",
            "-i", UPLOADED_MP3, "-ar", "24000", "-ac", "1", REF_WAV
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Also prepare short bilingual reference for "We touch."
    bi_wav = f"{WORK_DIR}/audio/ref_bilingual5s.wav"
    if not os.path.exists(bi_wav):
        subprocess.run([
            "ffmpeg", "-y", "-ss", "0.0", "-t", "7.45",
            "-i", UPLOADED_MP3, "-ar", "24000", "-ac", "1", bi_wav
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return REF_WAV, bi_wav


def main():
    t_all = time.time()
    ref_zh, ref_bi = prepare_reference()
    ref_bi_text = "Anthropic上市那天，在自己的YouTube频道上发了一支十五分钟的片子，叫The Making of Anthropic。"

    print("Loading F5-TTS v1 Base + Faster-Whisper QA model...")
    tts = F5TTS(model="F5TTS_v1_Base", device="cpu")
    wh = WhisperModel("small", device="cpu", compute_type="int8")

    chunks = []
    timeline = []
    cursor = 0.0

    for idx, (cid, act, gen_text, sub_text, speed, pre_p, post_p) in enumerate(CUES):
        if pre_p > 0:
            chunks.append(np.zeros(int(round(pre_p * SR)), dtype=np.float32))
            cursor += pre_p

        wav48 = f"{SEG_DIR}/{cid}_48k.wav"
        meta_json = f"{SEG_DIR}/{cid}.json"

        # Support resuming cached verified cues if re-run
        if os.path.exists(wav48) and os.path.exists(meta_json):
            rec_info = json.load(open(meta_json))
            print(f"[{idx+1:02d}/{len(CUES)}] {cid} CACHED (score={rec_info['score']:.2f}): {rec_info['asr']}")
        else:
            best_score = -1.0
            best_raw = None
            best_asr = ""
            best_words = []
            use_ref = ref_bi if cid == "a5_03" else ref_zh
            use_ref_txt = ref_bi_text if cid == "a5_03" else REF_TEXT

            for attempt in range(3):
                seed = 100 + idx * 17 + attempt * 31
                raw_out = f"{SEG_DIR}/{cid}_try{attempt}.wav"
                t0 = time.time()
                tts.infer(
                    ref_file=use_ref,
                    ref_text=use_ref_txt,
                    gen_text=gen_text,
                    nfe_step=18,
                    cfg_strength=2.0,
                    speed=speed,
                    seed=seed,
                    file_wave=raw_out,
                )
                # Trim leading/trailing silence cleanly and resample to 16k for Whisper QA
                clean_16k = f"{SEG_DIR}/{cid}_try{attempt}_16k.wav"
                subprocess.run([
                    "ffmpeg", "-y", "-i", raw_out,
                    "-af", "silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.04,areverse,silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.06,areverse",
                    "-ar", "16000", "-ac", "1", clean_16k
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                a16, _ = sf.read(clean_16k, dtype="float32")
                lang = "en" if cid == "a5_03" else "zh"
                segs, _ = wh.transcribe(a16, language=lang, word_timestamps=True)
                segs = list(segs)
                rec = "".join(s.text for s in segs).strip()
                words = []
                for s in segs:
                    for w in (s.words or []):
                        words.append({"s": round(w.start, 3), "e": round(w.end, 3), "w": w.word})
                sc = score_asr(gen_text, rec)
                dt = time.time() - t0
                print(f"[{idx+1:02d}/{len(CUES)}] {cid} try{attempt} ({dt:.1f}s, dur={len(a16)/16000:.2f}s, sc={sc:.2f}) -> '{rec}'")
                if sc > best_score:
                    best_score = sc
                    best_raw = raw_out
                    best_asr = rec
                    best_words = words
                if sc >= 0.78:
                    break

            # Convert best take to trimmed 48kHz mono WAV
            subprocess.run([
                "ffmpeg", "-y", "-i", best_raw,
                "-af", "silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.04,areverse,silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.06,areverse",
                "-ar", str(SR), "-ac", "1", wav48
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            rec_info = {"score": best_score, "asr": best_asr, "words": best_words}
            json.dump(rec_info, open(meta_json, "w", encoding="utf-8"), ensure_ascii=False)

        data, sr = sf.read(wav48, dtype="float32")
        assert sr == SR
        rms = np.sqrt(np.mean(data ** 2) + 1e-12)
        target_rms = 0.145 if act >= 3 else 0.135
        data = np.clip(data * (target_rms / rms), -0.95, 0.95)
        fade = min(int(0.018 * SR), len(data) // 4)
        data[:fade] *= np.linspace(0, 1, fade)
        data[-fade:] *= np.linspace(1, 0, fade)

        start_t = cursor
        dur = len(data) / SR
        end_t = start_t + dur
        chunks.append(data)
        cursor = end_t

        timeline.append({
            "id": cid,
            "act": act,
            "start": round(start_t, 3),
            "end": round(end_t, 3),
            "duration": round(dur, 3),
            "text": gen_text,
            "subtitle": sub_text,
            "post_pause": post_p,
            "asr_score": round(rec_info["score"], 3),
        })

        if post_p > 0:
            chunks.append(np.zeros(int(round(post_p * SR)), dtype=np.float32))
            cursor += post_p

    raw_voice = np.concatenate(chunks)
    raw_wav = f"{WORK_DIR}/audio/narration_raw.wav"
    master_wav = f"{WORK_DIR}/audio/narration_master.wav"
    sf.write(raw_wav, raw_voice, SR)

    # Studio documentary vocal chain tuned for warm human IVC clone
    af = (
        "highpass=f=75,"
        "equalizer=f=150:t=q:w=1.2:g=2.0,"
        "equalizer=f=420:t=q:w=1.5:g=-1.2,"
        "equalizer=f=3200:t=q:w=1.4:g=1.4,"
        "equalizer=f=6800:t=q:w=2.0:g=-1.8,"
        "acompressor=threshold=-20dB:ratio=2.3:attack=12:release=140:makeup=2,"
        "alimiter=limit=0.92,"
        "loudnorm=I=-16:TP=-1.5:LRA=9"
    )
    subprocess.run([
        "ffmpeg", "-y", "-i", raw_wav, "-af", af, "-ar", str(SR), "-ac", "2", master_wav
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    acts = {}
    for a in [1, 2, 3, 4, 5]:
        items = [x for x in timeline if x["act"] == a]
        acts[str(a)] = {
            "first_voice": items[0]["start"],
            "last_voice": items[-1]["end"],
            "end_with_pause": round(items[-1]["end"] + items[-1]["post_pause"], 3),
        }

    act1_end = acts["1"]["end_with_pause"]
    act2_end = acts["2"]["end_with_pause"]
    cliff_start = act2_end
    cliff_end = round(cliff_start + 1.50, 3)
    jcut_audio_start = round(cliff_end - 0.55, 3)
    act3_end = acts["3"]["end_with_pause"]
    act4_end = acts["4"]["end_with_pause"]
    total_dur = round(cursor, 3)

    meta = {
        "voice_source": "F5-TTS v1 Base zero-shot clone of uploaded ElevenLabs IVC voice",
        "total_duration": total_dur,
        "acts": {
            "1": {"start": 0.0, "end": act1_end, "name": "I. THE SMOOTHNESS", "cn": "第一幕 · 平滑的狂欢"},
            "2": {"start": act1_end, "end": act2_end, "name": "II. THE TONGUE", "cn": "第二幕 · 舌头的逻辑"},
            "cliff": {"start": cliff_start, "end": cliff_end, "jcut_audio_start": jcut_audio_start},
            "3": {"start": cliff_end, "end": act3_end, "name": "III. HANDWERKLICHKEIT", "cn": "第三幕 · 进入阻力"},
            "4": {"start": act3_end, "end": act4_end, "name": "IV. THE ROUGH EDGE", "cn": "第四幕 · 数字时代的毛边"},
            "5": {"start": act4_end, "end": total_dur, "name": "WE TOUCH.", "cn": "尾声 · 宣言"},
        },
        "cues": timeline,
    }
    with open(f"{WORK_DIR}/timeline.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # Generate Cinema ASS Subtitles
    def fmt_ass(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = t % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    def split_subtitle(text, start, end):
        if not text:
            return []
        if len(text) <= 22:
            return [(start, end, text.rstrip("，。、"))]
        parts = re.split(r'(?<=[，；：。？！——])', text)
        parts = [p for p in parts if p.strip()]
        merged = []
        for p in parts:
            if merged and len(merged[-1]) + len(p) <= 21 and not merged[-1].endswith(("。", "？", "！")):
                merged[-1] += p
            else:
                merged.append(p)
        total_chars = sum(len(x) for x in merged)
        res = []
        t = start
        for x in merged:
            dt = (end - start) * (len(x) / max(1, total_chars))
            res.append((t, t + dt, x.rstrip("，。、")))
            t += dt
        return res

    ass_header = """[Script Info]
Title: 别再谈品味了，聊聊手感
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: SubCold,Noto Sans CJK SC Medium,48,&H00F4F7FA,&H000000FF,&H50080C12,&H70000000,0,0,0,0,100,100,2.5,0,1,2.2,2.2,2,110,110,64,1
Style: SubWarm,Noto Serif CJK SC SemiBold,49,&H00FAF4EA,&H000000FF,&H48100C08,&H70000000,0,0,0,0,100,100,3.2,0,1,2.2,2.4,2,110,110,64,1
Style: ChapterCold,Inter,23,&H18E6EFF8,&H000000FF,&H60000000,&H80000000,0,0,0,0,100,100,5.5,0,1,1.4,1.2,7,84,84,54,1
Style: ChapterWarm,Noto Serif CJK SC Medium,23,&H18F6EAD8,&H000000FF,&H50100A06,&H80000000,0,0,0,0,100,100,5.0,0,1,1.4,1.2,7,84,84,54,1
Style: ConceptOverlay,Noto Serif CJK SC Bold,68,&H00FFF9F0,&H000000FF,&H300B0805,&H60000000,0,0,0,0,100,100,6.5,0,1,3.2,4.0,5,100,100,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    chapter_marks = [
        ("ChapterCold", 4.2, 8.8, "I  ·  THE SMOOTHNESS"),
        ("ChapterCold", act1_end + 0.5, act1_end + 5.0, "II  ·  THE TONGUE"),
        ("ChapterWarm", cliff_end + 1.0, cliff_end + 6.0, "III  ·  HANDWERKLICHKEIT"),
        ("ChapterWarm", act3_end + 0.6, act3_end + 5.2, "IV  ·  THE ROUGH EDGE"),
    ]
    for st, s_t, e_t, label in chapter_marks:
        events.append(f"Dialogue: 2,{fmt_ass(s_t)},{fmt_ass(e_t)},{st},,0,0,0,,{{\\fad(500,600)}}{label}")

    for c in timeline:
        if c["id"] == "a3_02":
            events.append(
                f"Dialogue: 2,{fmt_ass(c['start']+1.2)},{fmt_ass(c['end']+0.6)},ConceptOverlay,,0,0,0,,"
                f"{{\\fad(400,500)\\blur2.5\\an5\\pos(960,475)\\fnDejaVu Serif\\fs70\\fsp6}}Handwerklichkeit"
                f"\\N{{\\fnNoto Serif CJK SC Medium\\fs32\\fsp12\\alpha&H20&}}手 作 性"
            )
        elif c["id"] == "a3_06":
            events.append(
                f"Dialogue: 2,{fmt_ass(c['start']+0.4)},{fmt_ass(c['start']+3.6)},ConceptOverlay,,0,0,0,,"
                f"{{\\fad(350,500)\\blur2.5\\an5\\pos(960,460)\\fnNoto Serif CJK SC Bold\\fs78\\fsp20}}心 手 合 一"
            )

    for c in timeline:
        style = "SubCold" if c["act"] <= 2 else "SubWarm"
        for s_t, e_t, line in split_subtitle(c["subtitle"], c["start"], c["end"]):
            events.append(f"Dialogue: 1,{fmt_ass(s_t)},{fmt_ass(e_t)},{style},,0,0,0,,{{\\fad(120,140)}}{line}")

    ass_path = f"{WORK_DIR}/subs/subtitles.ass"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(events) + "\n")

    print(f"ALL DONE in {(time.time()-t_all)/60:.1f} min! Total duration: {total_dur:.2f}s ({total_dur/60:.2f} min)")
    for k, v in meta["acts"].items():
        print(f"  Act {k:5s}: {v['start']:6.2f}s -> {v['end']:6.2f}s")


if __name__ == "__main__":
    main()
