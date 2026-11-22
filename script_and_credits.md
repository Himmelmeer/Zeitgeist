# 《别再谈“品味”了，聊聊“手感”》—— 制作脚手架与素材署名

- **片长**：约 3 分 04 秒（184.3s）
- **画幅 / 规格**：1920×1080 · 30fps · H.264 High@4.1 · 48kHz Stereo AAC 256kbps（-14.6 LUFS，-0.9 dBFS True Peak）
- **配音来源**：基于用户上传的 ElevenLabs IVC 声音样本（`ElevenLabs_新IVC-中文1122_eleven_v4_stab0.4-style0.3.mp3`），使用 `F5-TTS v1 Base` 零样本克隆全片 25 组中英双语旁白，并逐句经由 Faster-Whisper 反向听写质检与广播级人声母带处理。
- **视听架构**：
  - **前半段（第一、二幕：0:00 – 1:09）**：冷峻低饱和青灰调色、无衬线字体（`Inter` + `Noto Sans CJK SC`）、高频电子低频 Drone 与清脆机械 UI 点击音，呈现零阻力的“平滑陷阱”与筛选逻辑。
  - **核心转折（1:08.94 – 1:10.44）**：全片电子音与画面瞬间硬切黑屏，1.5 秒真空寂静；画面亮起前 **0.55 秒 J-Cut** 提前切入真实木工凿木摩擦声。
  - **后半段（第三、四幕及尾声：1:10.44 – 3:04.29）**：温润柯达暖金胶片调色、细腻有机颗粒（Film Grain）、衬线字体（`Noto Serif CJK SC` + `DejaVu Serif`）；第三幕完全撤去配乐，保留高保真放大的真实物理摩擦声（木工凿刻、机械机芯擒纵微响、湿润陶泥拉坯、毛笔拖纸、手工打磨、揉面）；第四幕引入极简巴赫大提琴独奏（附轻微温暖磁带底噪）与帧级同步的机械键盘删改音，最终自然收束在萨拉班德舞曲悠长的低音和弦与 `We touch.` 上。

## 制作管线（可完整复现）

1. `scripts/01_generate_narration.py`：提取上传样本中的纯净语音参考，通过 `F5-TTS v1 Base` 零样本克隆全片旁白，逐句经 Faster-Whisper 反向听写校验（不达标自动换种子重试），经广播级人声母带 EQ/压缩/响度处理后输出精确时间轴 `timeline.json` 与分幕字体 `subtitles.ass`。
2. `scripts/02_render_custom_scenes.py`：基于 Headless Chrome 逐帧渲染 5 组 1080p@30fps 定制动效与交互画面（Keynote `TASTE` 巨字与硅谷金句流、`Regenerate` 机械点击循环、经典名画像素网格扫描、深夜暖光编辑器删除 AI 华丽句并亲手慢敲真诚短句、尾声 `We touch.` 与极简演职员表），并导出帧级同步音效时间戳 `ui_events.json`。
3. `scripts/shot_layout.py`：根据 `timeline.json` 动态计算全片 41 组镜头的统一时间锚点，确保画面切换、UI 交互与音效/配乐零漂移同步。
4. `scripts/03_synthesize_foley_and_mix.py`：多轨音效合成与声场混音（含语音包络侧链自动闪避 Sidechain Ducking、J-Cut 精准对齐、巴赫大提琴自然乐句收尾对齐、-14.6 LUFS 响度母带）。
5. `scripts/04_assemble_video.py`：41 镜头分幕调色、超采样平滑微推镜、隐形底部渐变暗幕、胶片颗粒与暗角合成、ASS 电影字幕烧录与高码率成片封装。

## 素材与音乐致谢（Credits）

- **配乐（第四幕 & 尾声）**：J.S. Bach — *Cello Suite No. 1 in G Major, BWV 1007: IV. Sarabande*，演奏：John Michel（Wikimedia Commons，CC BY）。
- **名画影像（第二幕像素拆解镜头）**：达·芬奇《蒙娜丽莎》、维米尔《戴珍珠耳环的少女》、梵高《星夜》、葛饰北斋《神奈川冲浪里》（Wikimedia Commons，Public Domain）。
- **实拍视频与基础音效**：Mixkit Free Stock Video & Free Sound Effects（Mixkit License，无水印商用授权）。
