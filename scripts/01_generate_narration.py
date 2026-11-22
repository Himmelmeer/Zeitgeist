#!/usr/bin/env python3
"""
Step 1: Generate mastered documentary narration with segment-level prosody,
warm broadcast vocal chain, exact timeline JSON, and cinema-grade ASS subtitles.
"""
import asyncio
import json
import os
import subprocess
import numpy as np
import soundfile as sf
import edge_tts

WORK_DIR = "/tmp/zeitgeist_work"
SEG_DIR = f"{WORK_DIR}/audio/segs"
os.makedirs(SEG_DIR, exist_ok=True)
os.makedirs(f"{WORK_DIR}/subs", exist_ok=True)

# (id, act, text, subtitle_text, voice, rate, pitch, pre_pause_s, post_pause_s)
CUES = [
    # --- ACT 1: 平滑的狂欢 (Starts after 4.0s cold visual hook) ---
    ("a1_01", 1,
     "这两年，科技圈和设计界最常挂在嘴边的词，叫 Taste，品味。",
     "这两年，科技圈和设计界最常挂在嘴边的词，叫 Taste —— 品味。",
     "zh-CN-YunyangNeural", "-4%", "-2Hz", 4.0, 0.55),
    ("a1_02", 1,
     "人们说，AI 已经接管了执行，未来人类唯一剩下的护城河，就是好品味。",
     "人们说，AI 已经接管了执行，未来人类唯一剩下的护城河，就是“好品味”。",
     "zh-CN-YunyangNeural", "-4%", "-2Hz", 0.0, 0.75),
    ("a1_03", 1,
     "听起来很体面。",
     "听起来很体面。",
     "zh-CN-YunyangNeural", "-7%", "-2Hz", 0.0, 0.85),
    ("a1_04", 1,
     "可每次听到这个词，我心里总会冒出一种奇怪的违和感。",
     "可每次听到这个词，我心里总会冒出一种奇怪的违和感。",
     "zh-CN-YunyangNeural", "-6%", "-2Hz", 0.0, 2.4),

    # --- ACT 2: 舌头的逻辑 ---
    ("a2_01", 2,
     "看看这个词本身吧。Taste，味觉，属于舌头。",
     "看看这个词本身吧。Taste，味觉，属于舌头。",
     "zh-CN-YunyangNeural", "-5%", "-2Hz", 1.8, 0.65),
    ("a2_02", 2,
     "它发生在一切已经完成之后。",
     "它发生在一切已经完成之后。",
     "zh-CN-YunyangNeural", "-6%", "-2Hz", 0.0, 0.60),
    ("a2_03", 2,
     "菜端上来了，你尝一口，给出一个判决：喜欢，或者讨厌；高级，或者庸俗。",
     "菜端上来了，你尝一口，给出一个判决：喜欢，或者讨厌；高级，或者庸俗。",
     "zh-CN-YunyangNeural", "-5%", "-2Hz", 0.0, 0.65),
    ("a2_04", 2,
     "如果不合胃口，吐掉就行。你的舌头，从来不需要去改造这道菜。",
     "如果不合胃口，吐掉就行。你的舌头，从来不需要去改造这道菜。",
     "zh-CN-YunyangNeural", "-5%", "-2Hz", 0.0, 0.90),
    ("a2_05", 2,
     "品味，是一种站在安全距离之外的筛选。它依赖的，是见多识广的数据库。",
     "品味是一种站在安全距离之外的筛选。它依赖的，是见多识广的数据库。",
     "zh-CN-YunyangNeural", "-5%", "-2Hz", 0.0, 0.85),
    ("a2_06", 2,
     "可问题是，今天，AI 已经吞下了全人类几千年的视觉、听觉和文本遗产。",
     "可问题是——今天，AI 已经吞下了全人类几千年的视觉、听觉和文本遗产。",
     "zh-CN-YunyangNeural", "-4%", "-2Hz", 0.0, 0.60),
    ("a2_07", 2,
     "如果仅仅是选出最体面、最符合高级审美的那个选项，算法正在以惊人的速度追平我们。",
     "如果仅仅是“选出最体面、最符合高级审美的那个选项”，算法正在以惊人的速度追平我们。",
     "zh-CN-YunyangNeural", "-4%", "-2Hz", 0.0, 0.85),
    ("a2_08", 2,
     "当每个人都在修炼好品味，世界反而变得越来越像。",
     "当每个人都在修炼“好品味”，世界反而变得越来越像。",
     "zh-CN-YunyangNeural", "-8%", "-3Hz", 0.0, 1.30),

    # --- CLIFF & ACT 3: 进入阻力 (1.5s dead black silence + 2.4s pure macro wood ASMR before voice) ---
    ("a3_01", 3,
     "如果让我换掉品味这个词，我选 Touch，手感。",
     "如果让我换掉“品味”这个词，我选 Touch —— 手感。",
     "zh-CN-YunyangNeural", "-8%", "-3Hz", 3.90, 0.85),
    ("a3_02", 3,
     "德语里有一个更沉甸甸的词，叫 Handwerklichkeit，手作性。",
     "德语里有一个更沉甸甸的词，叫 Handwerklichkeit —— 手作性。",
     "zh-CN-YunyangNeural", "-9%", "-3Hz", 0.0, 0.95),
    ("a3_03", 3,
     "舌头只负责消费结果，手，却必须伸进材料里。",
     "舌头只负责消费结果，手，却必须伸进材料里。",
     "zh-CN-YunyangNeural", "-8%", "-3Hz", 0.0, 0.90),
    ("a3_04", 3,
     "当你真正去触摸一样东西，世界是会推回来的。",
     "当你真正去触摸一样东西，世界是会推回来的。",
     "zh-CN-YunyangNeural", "-9%", "-3Hz", 0.0, 1.65),
    ("a3_05", 3,
     "木头有纹理的倔强，宣纸有吸墨的脾气，泥土有离心力的反抗。",
     "木头有纹理的倔强，宣纸有吸墨的脾气，泥土有离心力的反抗。",
     "zh-CN-YunyangNeural", "-8%", "-3Hz", 0.0, 0.70),
    ("a3_06", 3,
     "你施力，它抵抗；你微调，它变形。",
     "你施力，它抵抗；你微调，它变形。",
     "zh-CN-YunyangNeural", "-9%", "-3Hz", 0.0, 0.95),
    ("a3_07", 3,
     "就在这成百上千次的摩擦和拉锯里，发生了一件奇妙的事：",
     "就在这成百上千次的摩擦和拉锯里，发生了一件奇妙的事：",
     "zh-CN-YunyangNeural", "-7%", "-3Hz", 0.0, 0.55),
    ("a3_08", 3,
     "你在打磨材料，材料也在反向塑形你的神经系统。",
     "你在打磨材料，材料也在反向塑形你的神经系统。",
     "zh-CN-YunyangNeural", "-8%", "-3Hz", 0.0, 0.95),
    ("a3_09", 3,
     "中国人管这种状态叫，心手合一。",
     "中国人管这种状态叫“心手合一”。",
     "zh-CN-YunyangNeural", "-10%", "-3Hz", 0.0, 0.95),
    ("a3_10", 3,
     "那种长在肌肉记忆里的分寸感，靠看一万张参考图是学不会的。",
     "那种长在肌肉记忆里的分寸感，靠看一万张参考图是学不会的。",
     "zh-CN-YunyangNeural", "-7%", "-3Hz", 0.0, 0.65),
    ("a3_11", 3,
     "它只能从阻力里长出来。",
     "它只能从阻力里长出来。",
     "zh-CN-YunyangNeural", "-10%", "-3Hz", 0.0, 2.20),

    # --- ACT 4: 数字时代的毛边 ---
    ("a4_01", 4,
     "有人会说，AI 时代，我们早就隔着屏幕干活了，哪来的手作？",
     "有人会说，AI 时代，我们早就隔着屏幕干活了，哪来的手作？",
     "zh-CN-YunyangNeural", "-6%", "-2Hz", 1.50, 0.75),
    ("a4_02", 4,
     "可手感，从来不只属于木匠和陶工。",
     "可手感，从来不只属于木匠和陶工。",
     "zh-CN-YunyangNeural", "-8%", "-3Hz", 0.0, 0.90),
    ("a4_03", 4,
     "当 AI 把从意图到结果的距离压缩为零，给我们端上一盘盘毫无瑕疵的平滑产物时，",
     "当 AI 把从“意图”到“结果”的距离压缩为零，给我们端上一盘盘毫无瑕疵的平滑产物时，",
     "zh-CN-YunyangNeural", "-6%", "-2Hz", 0.0, 0.45),
    ("a4_04", 4,
     "真正的创作者依然能敏锐地察觉到：这里太滑了，那里太假了，这不像人说的话。",
     "真正的创作者依然能敏锐地察觉到：这里太滑了，那里太假了，这不像人说的话。",
     "zh-CN-YunyangNeural", "-7%", "-3Hz", 0.0, 1.85),
    ("a4_05", 4,
     "于是你停下来，亲手把那一点犹豫、那一点停顿、那一点带着个人体温的毛边拉回来。",
     "于是你停下来，亲手把那一点犹豫、那一点停顿、那一点带着个人体温的“毛边”拉回来。",
     "zh-CN-YunyangNeural", "-8%", "-3Hz", 0.0, 1.00),
    ("a4_06", 4,
     "在一个全面加速的时代，主动保留一点阻力，就是我们握紧方向盘的方式。",
     "在一个全面加速的时代，主动保留一点阻力，就是我们握紧方向盘的方式。",
     "zh-CN-YunyangNeural", "-8%", "-3Hz", 0.0, 2.00),

    # --- ACT 5: 尾声宣言 ---
    ("a5_01", 5,
     "评论家谈品味，创造者练手感。",
     "评论家谈品味，创造者练手感。",
     "zh-CN-YunyangNeural", "-10%", "-3Hz", 1.20, 1.15),
    ("a5_02", 5,
     "别只满足于做一个挑剔的旁观者。",
     "别只满足于做一个挑剔的旁观者。",
     "zh-CN-YunyangNeural", "-10%", "-3Hz", 0.0, 1.05),
    ("a5_03", 5,
     "伸出手，去碰触阻力，去留下指纹。",
     "伸出手，去碰触阻力，去留下指纹。",
     "zh-CN-YunyangNeural", "-12%", "-3Hz", 0.0, 1.80),
    ("a5_04", 5,
     "We touch.",
     "",
     "zh-CN-YunyangNeural", "-18%", "-4Hz", 0.0, 8.20),
]

SR = 48000

async def synth_one(cid, text, voice, rate, pitch):
    mp3_path = f"{SEG_DIR}/{cid}.mp3"
    wav_path = f"{SEG_DIR}/{cid}.wav"
    comm = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    await comm.save(mp3_path)
    # Decode to 48kHz mono wav and trim leading/trailing dead air cleanly
    subprocess.run([
        "ffmpeg", "-y", "-i", mp3_path,
        "-af", "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.04,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse",
        "-ar", str(SR), "-ac", "1", wav_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_path

async def main():
    print(f"Synthesizing {len(CUES)} narration segments...")
    # Synthesize concurrently in small batches
    tasks = []
    for c in CUES:
        tasks.append(synth_one(c[0], c[2], c[4], c[5], c[6]))
    wav_paths = await asyncio.gather(*tasks)

    # Assemble narration master track with exact timestamps
    chunks = []
    timeline = []
    cursor = 0.0

    for idx, (c, wp) in enumerate(zip(CUES, wav_paths)):
        cid, act, text, sub_text, voice, rate, pitch, pre_p, post_p = c
        if pre_p > 0:
            chunks.append(np.zeros(int(round(pre_p * SR)), dtype=np.float32))
            cursor += pre_p

        data, sr = sf.read(wp, dtype="float32")
        assert sr == SR
        # Normalize each segment lightly for consistent intimate proximity
        rms = np.sqrt(np.mean(data ** 2) + 1e-12)
        target_rms = 0.14 if act >= 3 else 0.13
        data = data * (target_rms / rms)
        data = np.clip(data, -0.95, 0.95)
        # Apply gentle 15ms fade in/out to avoid any clicks
        fade = min(int(0.015 * SR), len(data) // 4)
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
            "text": text,
            "subtitle": sub_text,
            "post_pause": post_p,
        })

        if post_p > 0:
            chunks.append(np.zeros(int(round(post_p * SR)), dtype=np.float32))
            cursor += post_p

    raw_voice = np.concatenate(chunks)
    raw_wav = f"{WORK_DIR}/audio/narration_raw.wav"
    master_wav = f"{WORK_DIR}/audio/narration_master.wav"
    sf.write(raw_wav, raw_voice, SR)

    # Studio documentary vocal chain:
    # - High-pass 75Hz (clean rumble)
    # - Warm chest resonance +2.2dB at 155Hz
    # - Slight boxy cut -1.5dB at 420Hz
    # - Subtle clarity presence +1.5dB at 3200Hz
    # - Gentle de-ess cut -2.0dB at 6800Hz
    # - Gentle broadcast compressor + limiter
    # - Normalized to -16 LUFS
    af = (
        "highpass=f=75,"
        "equalizer=f=155:t=q:w=1.2:g=2.4,"
        "equalizer=f=420:t=q:w=1.5:g=-1.5,"
        "equalizer=f=3200:t=q:w=1.4:g=1.4,"
        "equalizer=f=6800:t=q:w=2.0:g=-2.2,"
        "acompressor=threshold=-20dB:ratio=2.4:attack=12:release=140:makeup=2,"
        "alimiter=limit=0.92,"
        "loudnorm=I=-16:TP=-1.5:LRA=9"
    )
    subprocess.run([
        "ffmpeg", "-y", "-i", raw_wav, "-af", af, "-ar", str(SR), "-ac", "2", master_wav
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Compute act boundaries
    acts = {}
    for a in [1, 2, 3, 4, 5]:
        items = [x for x in timeline if x["act"] == a]
        acts[str(a)] = {
            "first_voice": items[0]["start"],
            "last_voice": items[-1]["end"],
            "end_with_pause": round(items[-1]["end"] + items[-1]["post_pause"], 3),
        }

    # Exact transition timestamps
    act1_end = acts["1"]["end_with_pause"]
    act2_end = acts["2"]["end_with_pause"]
    # The iconic 1.5s dead-black silence cliff starts at act2_end
    cliff_start = act2_end
    cliff_end = round(cliff_start + 1.50, 3)
    jcut_audio_start = round(cliff_end - 0.55, 3)  # Wood sound enters 0.55s BEFORE picture!
    act3_end = acts["3"]["end_with_pause"]
    act4_end = acts["4"]["end_with_pause"]
    total_dur = round(cursor, 3)

    meta = {
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

    print(f"Total duration: {total_dur:.2f}s ({total_dur/60:.2f} min)")
    for k, v in meta["acts"].items():
        print(f"  Act {k:5s}: {v['start']:6.2f}s -> {v['end']:6.2f}s")

    # Generate Cinema ASS Subtitles (Sans-serif for Acts 1-2, Serif for Acts 3-5!)
    def fmt_ass(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = t % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    def split_subtitle(text, start, end):
        """Split long Chinese lines naturally at punctuation so every subtitle is a clean single line."""
        if not text:
            return []
        if len(text) <= 22:
            return [(start, end, text)]
        # Split on Chinese commas/semicolons/colons/em-dashes
        import re
        parts = re.split(r'(?<=[，；：。？！——])', text)
        parts = [p for p in parts if p.strip()]
        # Merge tiny fragments
        merged = []
        for p in parts:
            if merged and len(merged[-1]) + len(p) <= 21:
                merged[-1] += p
            else:
                merged.append(p)
        # Strip trailing commas/periods for cleaner cinema subtitles
        total_chars = sum(len(x) for x in merged)
        res = []
        t = start
        for x in merged:
            frac = len(x) / max(1, total_chars)
            dt = (end - start) * frac
            clean = x.rstrip("，。、")
            res.append((t, t + dt, clean))
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
    # Minimalist cinema chapter markers in upper-left corner (fade in/out smoothly)
    chapter_marks = [
        ("ChapterCold", 4.2, 8.8, "I  ·  THE SMOOTHNESS"),
        ("ChapterCold", act1_end + 0.5, act1_end + 5.0, "II  ·  THE TONGUE"),
        ("ChapterWarm", cliff_end + 1.0, cliff_end + 6.0, "III  ·  HANDWERKLICHKEIT"),
        ("ChapterWarm", act3_end + 0.6, act3_end + 5.2, "IV  ·  THE ROUGH EDGE"),
    ]
    for st, s_t, e_t, label in chapter_marks:
        events.append(f"Dialogue: 2,{fmt_ass(s_t)},{fmt_ass(e_t)},{st},,0,0,0,,{{\\fad(500,600)}}{label}")

    # Subtle typographic accent when "Handwerklichkeit" & "心手合一" are spoken
    for c in timeline:
        if c["id"] == "a3_02":
            events.append(
                f"Dialogue: 2,{fmt_ass(c['start']+1.4)},{fmt_ass(c['end']+0.6)},ConceptOverlay,,0,0,0,,"
                f"{{\\fad(400,500)\\blur2.5\\an5\\pos(960,475)\\fnDejaVu Serif\\fs70\\fsp6}}Handwerklichkeit"
                f"\\N{{\\fnNoto Serif CJK SC Medium\\fs32\\fsp12\\alpha&H20&}}手 作 性"
            )
        elif c["id"] == "a3_09":
            events.append(
                f"Dialogue: 2,{fmt_ass(c['start']+1.2)},{fmt_ass(c['end']+0.7)},ConceptOverlay,,0,0,0,,"
                f"{{\\fad(350,500)\\blur2.5\\an5\\pos(960,460)\\fnNoto Serif CJK SC Bold\\fs78\\fsp20}}心 手 合 一"
            )

    # Dialogue subtitles
    for c in timeline:
        style = "SubCold" if c["act"] <= 2 else "SubWarm"
        subs = split_subtitle(c["subtitle"], c["start"], c["end"])
        for s_t, e_t, line in subs:
            clean = line.rstrip("，。、")
            events.append(f"Dialogue: 1,{fmt_ass(s_t)},{fmt_ass(e_t)},{style},,0,0,0,,{{\\fad(120,140)}}{clean}")

    ass_path = f"{WORK_DIR}/subs/subtitles.ass"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(events) + "\n")
    print("Wrote:", ass_path)

if __name__ == "__main__":
    asyncio.run(main())
