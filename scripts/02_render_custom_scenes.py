#!/usr/bin/env python3
"""
Step 2: Deterministically render 5 cinema-grade 1920x1080@30fps custom motion-graphics
and UI interaction scenes using headless Google Chrome + Playwright frame stepping.
Also outputs exact frame-synced SFX event timestamps (clicks, delete, keystrokes)
to /tmp/zeitgeist_work/ui_events.json.
"""
import base64
import json
import os
import subprocess
from playwright.sync_api import sync_playwright

WORK_DIR = "/tmp/zeitgeist_work"
OUT_DIR = f"{WORK_DIR}/ui_renders"
os.makedirs(OUT_DIR, exist_ok=True)
FPS = 30


def render_html_to_mp4(browser, html_content, duration_s, out_mp4):
    total_frames = int(round(duration_s * FPS))
    page = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
    page.set_content(html_content, wait_until="load")
    # Wait for fonts to be ready
    page.evaluate("() => document.fonts.ready")

    cmd = [
        "ffmpeg", "-y",
        "-f", "image2pipe", "-vcodec", "png", "-framerate", str(FPS),
        "-i", "-",
        "-c:v", "libx264", "-preset", "medium", "-crf", "16",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        out_mp4,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for f in range(total_frames):
        t = f / FPS
        page.evaluate(f"window.renderAt({t:.6f})")
        png = page.screenshot(type="png")
        proc.stdin.write(png)
    proc.stdin.close()
    ret = proc.wait()
    page.close()
    if ret != 0:
        raise RuntimeError(f"ffmpeg failed for {out_mp4}")
    print(f"Rendered {out_mp4} ({total_frames} frames, {duration_s:.2f}s)")


def img_b64(path):
    with open(path, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("ascii")


def scene_act1_taste_wall():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* { margin:0; padding:0; box-sizing:border-box; }
body { width:1920px; height:1080px; overflow:hidden; background:#05070b; color:#edf2f7; font-family:'Inter','Noto Sans CJK SC',sans-serif; }
.stage { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center;
  background: radial-gradient(ellipse 65% 55% at 50% 35%, rgba(88,132,190,0.22), rgba(5,7,11,0.98) 72%); }
.eyebrow { font-family:'JetBrains Mono',monospace; font-size:20px; letter-spacing:9px; color:rgba(170,200,235,0.65); margin-bottom:28px; text-transform:uppercase; }
.big-taste { font-size:235px; font-weight:700; letter-spacing:26px; color:#f4f8fc;
  text-shadow: 0 0 80px rgba(130,185,255,0.28); transform-origin:center; }
.subline { margin-top:34px; font-size:26px; font-weight:400; letter-spacing:6px; color:rgba(215,228,242,0.55); }
.feed { position:absolute; inset:0; background:#070a0f; display:none; padding:60px 140px; }
.feed-grid { display:grid; grid-template-columns:1fr 1fr; gap:36px; width:100%; }
.card { background:linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.02));
  border:1px solid rgba(180,210,245,0.12); border-radius:20px; padding:42px 44px;
  box-shadow:0 24px 60px rgba(0,0,0,0.45); }
.meta { font-family:'JetBrains Mono',monospace; font-size:17px; color:rgba(135,175,225,0.75); margin-bottom:18px; letter-spacing:1.5px; }
.quote { font-size:36px; line-height:1.38; font-weight:600; color:#eef4fa; letter-spacing:-0.3px; }
.tag { margin-top:22px; font-size:18px; color:rgba(195,212,232,0.5); }
.hl { color:#8ec5ff; }
.vignette { position:absolute; inset:0; pointer-events:none;
  background:radial-gradient(ellipse at center, transparent 52%, rgba(0,0,0,0.75) 100%); }
</style></head><body>
<div class="stage" id="stage">
  <div class="eyebrow" id="eyebrow">DESIGN &amp; AI SUMMIT · KEYNOTE</div>
  <div class="big-taste" id="big">TASTE</div>
  <div class="subline" id="sub">THE ONLY REMAINING MOAT</div>
</div>
<div class="feed" id="feed">
  <div class="feed-grid" id="grid">
    <div class="card"><div class="meta">@silicon_vc · 142K VIEWS</div><div class="quote">“<span class="hl">Taste</span> is the new moat in the age of infinite AI generation.”</div><div class="tag">♥ 18.4K · ↻ 4.2K</div></div>
    <div class="card"><div class="meta">DESIGN PODCAST #219</div><div class="quote">“Execution is free now. The only thing that matters is <span class="hl">good taste</span>.”</div><div class="tag">♥ 12.1K · ↻ 3.1K</div></div>
    <div class="card"><div class="meta">AI PRODUCT WEEKLY</div><div class="quote">“Everyone can generate 1,000 options. Winners simply have <span class="hl">better taste</span>.”</div><div class="tag">♥ 9.8K · ↻ 2.7K</div></div>
    <div class="card"><div class="meta">CREATIVE DIRECTOR NOTE</div><div class="quote">“We are all curators now. Train your <span class="hl">taste</span>, automate the rest.”</div><div class="tag">♥ 24.6K · ↻ 6.9K</div></div>
    <div class="card"><div class="meta">FOUNDER ESSAY · TRENDING</div><div class="quote">“When code costs zero, <span class="hl">taste</span> becomes the ultimate leverage.”</div><div class="tag">♥ 31.2K · ↻ 8.4K</div></div>
    <div class="card"><div class="meta">AESTHETIC INDEX · 2026</div><div class="quote">“Minimalist. Effortless. Curated. Frictionless <span class="hl">taste</span> at scale.”</div><div class="tag">♥ 15.9K · ↻ 3.8K</div></div>
    <div class="card"><div class="meta">FUTURE OF WORK</div><div class="quote">“Don't touch the pixels. Just judge the output with <span class="hl">taste</span>.”</div><div class="tag">♥ 11.3K · ↻ 2.2K</div></div>
    <div class="card"><div class="meta">KEYNOTE CLIP</div><div class="quote">“<span class="hl">Taste</span> is the moat. <span class="hl">Taste</span> is everything.”</div><div class="tag">♥ 42.0K · ↻ 11.5K</div></div>
  </div>
</div>
<div class="vignette"></div>
<script>
window.renderAt = function(t) {
  const stage = document.getElementById('stage');
  const feed = document.getElementById('feed');
  const big = document.getElementById('big');
  const grid = document.getElementById('grid');
  if (t < 2.8) {
    stage.style.display = 'flex';
    feed.style.display = 'none';
    const p = t / 2.8;
    const scale = 0.96 + 0.08 * p;
    big.style.transform = `scale(${scale.toFixed(4)})`;
    big.style.letterSpacing = (22 + 16 * p).toFixed(2) + 'px';
    stage.style.opacity = Math.min(1, t / 0.25).toFixed(3);
  } else {
    stage.style.display = 'none';
    feed.style.display = 'block';
    const dt = t - 2.8;
    const y = -dt * 235;
    grid.style.transform = `translateY(${y.toFixed(1)}px)`;
  }
};
</script></body></html>"""


def scene_act2_regenerate():
    # Exact click timestamps within this 7.5s clip: 1.15s, 2.75s, 4.30s, 5.75s
    click_times = [1.15, 2.75, 4.30, 5.75]
    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* { margin:0; padding:0; box-sizing:border-box; }
body { width:1920px; height:1080px; overflow:hidden; background:#090c11; color:#e6edf5;
  font-family:'Inter','Noto Sans CJK SC',sans-serif; display:flex; align-items:center; justify-content:center; }
.window { width:1260px; background:#10151e; border:1px solid rgba(175,205,240,0.14);
  border-radius:22px; padding:48px 56px; box-shadow:0 40px 120px rgba(0,0,0,0.65); position:relative; }
.topbar { display:flex; align-items:center; justify-content:space-between; padding-bottom:24px;
  border-bottom:1px solid rgba(255,255,255,0.07); margin-bottom:34px; }
.dots { display:flex; gap:10px; }
.dot { width:13px; height:13px; border-radius:50%; background:rgba(255,255,255,0.18); }
.model { font-family:'JetBrains Mono',monospace; font-size:17px; color:rgba(155,185,220,0.65); letter-spacing:1.2px; }
.prompt { background:rgba(255,255,255,0.04); border-radius:14px; padding:20px 26px;
  font-size:24px; color:rgba(220,232,245,0.72); margin-bottom:34px; }
.response { min-height:220px; font-size:30px; line-height:1.68; color:#f1f6fc; font-weight:400; }
.bar { margin-top:36px; display:flex; align-items:center; justify-content:space-between; }
.btn { display:inline-flex; align-items:center; gap:12px; padding:15px 28px; border-radius:12px;
  background:rgba(120,175,255,0.12); border:1px solid rgba(135,188,255,0.38); color:#b8d9ff;
  font-size:21px; font-weight:500; letter-spacing:0.5px; transition:none; }
.btn.pressed { background:rgba(120,175,255,0.32); transform:scale(0.95); color:#ffffff; border-color:#8ec5ff; }
.counter { font-family:'JetBrains Mono',monospace; font-size:18px; color:rgba(150,175,205,0.55); }
.cursor { position:absolute; width:36px; height:36px; pointer-events:none; z-index:20;
  filter:drop-shadow(0 4px 10px rgba(0,0,0,0.6)); }
.ripple { position:absolute; width:64px; height:64px; border-radius:50%;
  border:2px solid rgba(145,200,255,0.85); pointer-events:none; opacity:0; }
</style></head><body>
<div class="window" id="win">
  <div class="topbar">
    <div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
    <div class="model">AESTHETIC GENERATOR · ZERO-FRICTION MODE</div>
  </div>
  <div class="prompt">生成一段极简、高级、有品味的产品宣言。</div>
  <div class="response" id="resp"></div>
  <div class="bar">
    <div class="btn" id="btn">↻ &nbsp;Regenerate</div>
    <div class="counter" id="cnt">VARIANT 01 / ∞ · 0.14s</div>
  </div>
</div>
<div class="ripple" id="ripple"></div>
<svg class="cursor" id="cur" viewBox="0 0 28 28"><path d="M4 2 L4 22 L10 17 L14.5 25 L17.5 23.5 L13 15.5 L20.5 15.5 Z" fill="#ffffff" stroke="#090c11" stroke-width="1.8"/></svg>
<script>
const variants = [
  "在极简与克制之间，重新定义当代生活的优雅边界，让每一次体验都臻于完美。",
  "以超越时代的审美洞察，雕琢纯粹而精致的感官哲学，成就非凡格调。",
  "化繁为简，于无声处见质感——用恰到好处的留白，诠释真正的现代高级感。",
  "融合先锋设计与温润美学，为追求极致品味的你，呈现毫无瑕疵的理想范式。",
  "告别冗余与喧嚣，回归纯粹本质，以克制的优雅唤醒你对精致生活的无限想象。"
];
const clicks = [1.15, 2.75, 4.30, 5.75];
window.renderAt = function(t) {
  const resp = document.getElementById('resp');
  const btn = document.getElementById('btn');
  const cnt = document.getElementById('cnt');
  const cur = document.getElementById('cur');
  const ripple = document.getElementById('ripple');

  // Determine active variant
  let vi = 0;
  let lastClick = -10;
  for (let i = 0; i < clicks.length; i++) {
    if (t >= clicks[i]) { vi = i + 1; lastClick = clicks[i]; }
  }
  const dt = t - lastClick;
  const fullText = variants[vi];
  // Ultra-fast AI streaming after each click (completes in 0.45s)
  const chars = vi === 0 ? fullText.length : Math.min(fullText.length, Math.floor((dt / 0.42) * fullText.length));
  resp.textContent = fullText.slice(0, chars);
  cnt.textContent = `VARIANT 0${vi+1} / ∞ · 0.1${(vi*3+2)%9}s`;

  // Cursor glides to button at (485, 735)
  const bx = 485, by = 735;
  let cx = bx, cy = by;
  if (t < 0.95) {
    const p = t / 0.95;
    const ease = 1 - Math.pow(1 - p, 3);
    cx = 920 + (bx - 920) * ease;
    cy = 520 + (by - 520) * ease;
  } else {
    // subtle impatient micro-bobbing on button
    cy = by + Math.sin(t * 7) * 2.5;
  }
  cur.style.left = cx + 'px';
  cur.style.top = cy + 'px';

  // Pressed state + ripple on click
  let pressed = false;
  let ripOp = 0, ripScale = 0.4;
  for (const c of clicks) {
    if (t >= c && t < c + 0.14) pressed = true;
    if (t >= c && t < c + 0.45) {
      const rp = (t - c) / 0.45;
      ripOp = (1 - rp) * 0.8;
      ripScale = 0.4 + rp * 1.6;
    }
  }
  btn.className = pressed ? 'btn pressed' : 'btn';
  ripple.style.left = (bx - 24) + 'px';
  ripple.style.top = (by - 24) + 'px';
  ripple.style.opacity = ripOp.toFixed(3);
  ripple.style.transform = `scale(${ripScale.toFixed(3)})`;
};
</script></body></html>"""
    return html, click_times


def scene_act2_pixel_grid():
    art_dir = f"{WORK_DIR}/raw/art"
    imgs = [
        ("MONA LISA · 1503", img_b64(f"{art_dir}/mona_lisa.jpg")),
        ("VERMEER · 1665", img_b64(f"{art_dir}/pearl_earring.jpg")),
        ("VAN GOGH · 1889", img_b64(f"{art_dir}/starry_night.jpg")),
        ("HOKUSAI · 1831", img_b64(f"{art_dir}/great_wave.jpg")),
    ]
    imgs_json = json.dumps(imgs)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ width:1920px; height:1080px; overflow:hidden; background:#05080d; font-family:'JetBrains Mono',monospace; }}
canvas {{ display:block; width:1920px; height:1080px; }}
</style></head><body>
<canvas id="c" width="1920" height="1080"></canvas>
<script>
const specs = {imgs_json};
const loaded = [];
let readyCount = 0;
specs.forEach((s, i) => {{
  const im = new Image();
  im.src = s[1];
  im.onload = () => {{ readyCount++; }};
  loaded.push({{ title: s[0], img: im }});
}});
const ctx = document.getElementById('c').getContext('2d');

window.renderAt = function(t) {{
  ctx.fillStyle = '#05080d';
  ctx.fillRect(0, 0, 1920, 1080);

  // Switch artworks faster as time progresses (accelerating consumption)
  let idx = 0;
  let localT = t;
  if (t < 2.2) {{ idx = 0; localT = t / 2.2; }}
  else if (t < 4.2) {{ idx = 1; localT = (t - 2.2) / 2.0; }}
  else if (t < 6.0) {{ idx = 2; localT = (t - 4.2) / 1.8; }}
  else {{ idx = Math.floor((t - 6.0) / 0.55) % 4; localT = ((t - 6.0) % 0.55) / 0.55; }}

  const item = loaded[idx];
  const im = item.img;
  if (im && im.complete && im.naturalWidth) {{
    // Fit nicely in center with cinematic scale
    const scale = Math.max(1920 / im.naturalWidth, 1080 / im.naturalHeight) * (1.03 + 0.04 * localT);
    const dw = im.naturalWidth * scale;
    const dh = im.naturalHeight * scale;
    const dx = (1920 - dw) / 2;
    const dy = (1080 - dh) / 2;
    ctx.save();
    ctx.filter = 'saturate(0.72) contrast(1.08) brightness(0.76)';
    ctx.drawImage(im, dx, dy, dw, dh);
    ctx.restore();
  }}

  // Cold cyan pixel grid & scanline ingestion overlay
  const scanY = (localT * 1.15) * 1080;
  const cell = 64;
  ctx.strokeStyle = 'rgba(110, 190, 255, 0.22)';
  ctx.lineWidth = 1;
  for (let x = 0; x <= 1920; x += cell) {{
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, Math.min(1080, scanY)); ctx.stroke();
  }}
  for (let y = 0; y <= Math.min(1080, scanY); y += cell) {{
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(1920, y); ctx.stroke();
  }}

  // Sample tokenized cells above scanline
  ctx.font = '12px JetBrains Mono';
  for (let y = 24; y < Math.min(1040, scanY - 20); y += cell * 2) {{
    for (let x = 14; x < 1880; x += cell * 3) {{
      const h = Math.abs(Math.sin(x * 12.9898 + y * 78.233 + idx * 19.1) * 43758.5453) % 1;
      if (h > 0.55) {{
        ctx.fillStyle = 'rgba(145, 212, 255, 0.14)';
        ctx.fillRect(x - 14, y - 24, cell, cell);
        ctx.fillStyle = 'rgba(175, 225, 255, 0.72)';
        ctx.fillText(h.toFixed(2), x, y + 14);
      }}
    }}
  }}

  // Bright scanline beam
  if (scanY < 1080) {{
    const grad = ctx.createLinearGradient(0, scanY - 90, 0, scanY + 6);
    grad.addColorStop(0, 'rgba(110, 200, 255, 0)');
    grad.addColorStop(0.92, 'rgba(130, 215, 255, 0.35)');
    grad.addColorStop(1, 'rgba(210, 242, 255, 0.95)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, scanY - 90, 1920, 96);
  }}

  // Minimal technical HUD metadata
  ctx.fillStyle = 'rgba(6, 10, 16, 0.72)';
  ctx.fillRect(72, 62, 540, 62);
  ctx.strokeStyle = 'rgba(130, 200, 255, 0.45)';
  ctx.strokeRect(72, 62, 540, 62);
  ctx.fillStyle = '#bfe2ff';
  ctx.font = '20px JetBrains Mono';
  ctx.fillText(`INGESTING // ${{item.title}}`, 94, 99);

  ctx.fillStyle = 'rgba(6, 10, 16, 0.72)';
  ctx.fillRect(1420, 62, 428, 62);
  ctx.strokeStyle = 'rgba(130, 200, 255, 0.45)';
  ctx.strokeRect(1420, 62, 428, 62);
  ctx.fillStyle = '#8ec5ff';
  ctx.fillText(`AESTHETIC_SCORE: 0.${{972 + idx * 6}}`, 1444, 99);

  // Subtle dark vignette
  const vg = ctx.createRadialGradient(960, 540, 350, 960, 540, 1150);
  vg.addColorStop(0, 'rgba(0,0,0,0)');
  vg.addColorStop(1, 'rgba(0,0,0,0.68)');
  ctx.fillStyle = vg;
  ctx.fillRect(0, 0, 1920, 1080);
}};
</script></body></html>"""


def scene_act4_rough_edge_editor():
    # Authentic human typing choreography (timestamps in seconds within this 15.5s shot)
    # 0.0 - 2.3s: Polished AI sentence sits on warm screen, cursor blinks
    # 2.3 - 4.0s: Selection sweeps across the slick sentence
    # 4.35s: DELETE!
    # 5.20s - 13.6s: Human slowly types "其实我只是想，亲手把这件事做对。" with a tiny authentic hesitation + 1 backspace!
    delete_time = 4.35
    typing_steps = [
        (5.30, "其"),
        (5.68, "其实"),
        (6.02, "其实我"),
        (6.48, "其实我只"),
        (6.82, "其实我只是"),
        (7.24, "其实我只是想"),
        (7.72, "其实我只是想，"),
        # small human breath pause (0.75s)
        (8.55, "其实我只是想，亲"),
        (8.92, "其实我只是想，亲手"),
        (9.35, "其实我只是想，亲手把"),
        (9.72, "其实我只是想，亲手把这"),
        (10.10, "其实我只是想，亲手把这见"),  # tiny authentic typo!
        (10.65, "其实我只是想，亲手把这"),    # backspace!
        (11.12, "其实我只是想，亲手把这件"),
        (11.50, "其实我只是想，亲手把这件事"),
        (11.98, "其实我只是想，亲手把这件事做"),
        (12.42, "其实我只是想，亲手把这件事做对"),
        (12.95, "其实我只是想，亲手把这件事做对。"),
    ]
    key_times = [s[0] for s in typing_steps]
    steps_json = json.dumps(typing_steps, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ width:1920px; height:1080px; overflow:hidden; background:#110e0b;
  font-family:'Noto Serif CJK SC','DejaVu Serif',serif; display:flex; align-items:center; justify-content:center;
  position:relative; }}
.lamp-glow {{ position:absolute; inset:0;
  background: radial-gradient(ellipse 75% 65% at 24% 18%, rgba(235,168,92,0.16), rgba(18,14,10,0.96) 72%); }}
.paper-frame {{ width:1360px; min-height:540px; padding:88px 104px; position:relative; z-index:2;
  background: linear-gradient(155deg, rgba(34,28,22,0.92), rgba(21,17,14,0.96));
  border: 1px solid rgba(235,192,135,0.14); border-radius:16px;
  box-shadow: 0 40px 120px rgba(0,0,0,0.72), inset 0 1px 0 rgba(255,220,175,0.08); }}
.doc-head {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:58px;
  font-family:'JetBrains Mono',monospace; font-size:16px; letter-spacing:2px; color:rgba(218,188,150,0.42); }}
.status-pill {{ padding:5px 14px; border-radius:99px; border:1px solid rgba(220,185,140,0.2); }}
.editor-body {{ font-size:42px; line-height:1.82; letter-spacing:1.8px; color:#f3e8d8; min-height:240px; }}
.ai-text {{ color:rgba(232,226,218,0.78); font-family:'Noto Sans CJK SC',sans-serif; font-weight:300; }}
.sel {{ background:rgba(222,162,88,0.34); color:#fff5e6; border-radius:4px; padding:2px 0; }}
.human-text {{ color:#fbf3e6; font-family:'Noto Serif CJK SC',serif; font-weight:500; }}
.caret {{ display:inline-block; width:3px; height:48px; background:#e7aa62; vertical-align:-9px; margin-left:4px;
  box-shadow:0 0 12px rgba(231,170,98,0.65); }}
.vignette {{ position:absolute; inset:0; pointer-events:none; z-index:5;
  background:radial-gradient(ellipse at center, transparent 48%, rgba(0,0,0,0.76) 100%); }}
</style></head><body>
<div class="lamp-glow"></div>
<div class="paper-frame" id="frame">
  <div class="doc-head">
    <span id="fname">DRAFT_04.MD</span>
    <span class="status-pill" id="pill">AI GENERATED · POLISHED</span>
  </div>
  <div class="editor-body" id="body"></div>
</div>
<div class="vignette"></div>
<script>
const aiStr = "在这个算法重塑一切的时代，我们更应当以优雅而克制的审美洞察，赋能每一次创意表达，成就非凡的品质与格调。";
const steps = {steps_json};
const delT = {delete_time};

window.renderAt = function(t) {{
  const body = document.getElementById('body');
  const pill = document.getElementById('pill');
  const frame = document.getElementById('frame');

  // Subtle breathing camera push-in (1.0 -> 1.035)
  const sc = 1.0 + 0.035 * (t / 15.5);
  frame.style.transform = `scale(${{sc.toFixed(4)}})`;

  const blink = (Math.floor(t * 2.1) % 2 === 0);
  const caretHtml = `<span class="caret" style="opacity:${{blink ? 1 : 0.12}}"></span>`;

  if (t < 2.2) {{
    pill.textContent = "AI GENERATED · POLISHED";
    body.innerHTML = `<span class="ai-text">${{aiStr}}</span>${{caretHtml}}`;
  }} else if (t < delT) {{
    pill.textContent = "SELECTING...";
    const p = Math.min(1, (t - 2.2) / 1.75);
    const ease = p < 0.5 ? 2*p*p : 1 - Math.pow(-2*p+2, 2)/2;
    const selLen = Math.floor(ease * aiStr.length);
    const left = aiStr.slice(0, aiStr.length - selLen);
    const right = aiStr.slice(aiStr.length - selLen);
    body.innerHTML = `<span class="ai-text">${{left}}<span class="sel">${{right}}</span></span>`;
  }} else if (t < 5.25) {{
    pill.textContent = "MANUAL · HUMAN";
    pill.style.borderColor = "rgba(235,175,98,0.45)";
    pill.style.color = "rgba(242,202,148,0.85)";
    body.innerHTML = caretHtml;
  }} else {{
    pill.textContent = "MANUAL · HUMAN";
    pill.style.borderColor = "rgba(235,175,98,0.45)";
    pill.style.color = "rgba(242,202,148,0.85)";
    let curText = "";
    let justTyped = false;
    for (const [st, txt] of steps) {{
      if (t >= st) {{
        curText = txt;
        if (t - st < 0.25) justTyped = true;
      }}
    }}
    const showCaret = justTyped || blink;
    body.innerHTML = `<span class="human-text">${{curText}}</span><span class="caret" style="opacity:${{showCaret ? 1 : 0.12}}"></span>`;
  }}
}};
</script></body></html>"""
    return html, delete_time, key_times


def scene_finale_we_touch():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* { margin:0; padding:0; box-sizing:border-box; }
body { width:1920px; height:1080px; overflow:hidden; background:#050505;
  display:flex; flex-direction:column; align-items:center; justify-content:center; position:relative; }
.glow { position:absolute; inset:0;
  background:radial-gradient(circle at 50% 50%, rgba(215,175,120,0.08), rgba(5,5,5,1) 62%); }
.title { font-family:'DejaVu Serif','Noto Serif CJK SC',serif; font-size:108px; font-weight:400;
  color:#f5ede0; letter-spacing:8px; position:relative; z-index:2; opacity:0; }
.credits { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center;
  z-index:3; opacity:0; text-align:center; }
.c-main { font-family:'Noto Serif CJK SC',serif; font-size:44px; letter-spacing:10px; color:#f2e8d9; margin-bottom:20px; }
.c-sub { font-family:'JetBrains Mono',monospace; font-size:17px; letter-spacing:7px; color:rgba(220,196,162,0.58); margin-bottom:54px; }
.c-line { width:64px; height:1px; background:rgba(220,196,162,0.32); margin-bottom:44px; }
.c-meta { font-family:'Noto Sans CJK SC',sans-serif; font-size:18px; line-height:2.1; letter-spacing:1.5px; color:rgba(215,205,190,0.48); }
</style></head><body>
<div class="glow" id="glow"></div>
<div class="title" id="title">We touch.</div>
<div class="credits" id="credits">
  <div class="c-main">别再谈“品味”了，聊聊“手感”</div>
  <div class="c-sub">TOUCH &nbsp;·&nbsp; HANDWERKLICHKEIT</div>
  <div class="c-line"></div>
  <div class="c-meta">
    Music — J.S. Bach, Cello Suite No. 1 in G Major, IV. Sarabande (John Michel, CC BY)<br>
    Visuals &amp; Foley Archive — Mixkit &amp; Wikimedia Commons
  </div>
</div>
<script>
window.renderAt = function(t) {
  const title = document.getElementById('title');
  const credits = document.getElementById('credits');
  const glow = document.getElementById('glow');

  // 0.0 - 0.8s: quiet dark breath
  // 0.8 - 5.2s: "We touch." gently emerges and breathes open
  // 5.2 - 9.5s: graceful minimal end credits -> fade to black
  let tOp = 0;
  if (t >= 0.6 && t < 2.0) tOp = (t - 0.6) / 1.4;
  else if (t >= 2.0 && t < 4.5) tOp = 1.0;
  else if (t >= 4.5 && t < 5.5) tOp = Math.max(0, 1 - (t - 4.5) / 1.0);
  title.style.opacity = tOp.toFixed(3);
  title.style.letterSpacing = (6 + Math.max(0, t - 0.6) * 1.1).toFixed(2) + 'px';

  let cOp = 0;
  if (t >= 5.5 && t < 6.4) cOp = (t - 5.5) / 0.9;
  else if (t >= 6.4 && t < 8.4) cOp = 1.0;
  else if (t >= 8.4 && t < 9.3) cOp = Math.max(0, 1 - (t - 8.4) / 0.9);
  credits.style.opacity = cOp.toFixed(3);
  glow.style.opacity = Math.max(tOp, cOp * 0.7).toFixed(3);
};
</script></body></html>"""


def main():
    events = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/usr/local/bin/google-chrome",
            args=["--no-sandbox", "--disable-gpu-sandbox", "--headless=new"],
        )
        # 1. Act 1 Taste Wall (6.5s)
        render_html_to_mp4(browser, scene_act1_taste_wall(), 6.5, f"{OUT_DIR}/ui_act1_taste_wall.mp4")

        # 2. Act 2 Regenerate Loop (7.5s)
        h2, clicks = scene_act2_regenerate()
        events["act2_regenerate_clicks"] = clicks
        render_html_to_mp4(browser, h2, 7.5, f"{OUT_DIR}/ui_act2_regenerate.mp4")

        # 3. Act 2 Pixel Grid Ingestion (8.5s)
        render_html_to_mp4(browser, scene_act2_pixel_grid(), 8.5, f"{OUT_DIR}/ui_act2_pixel_grid.mp4")

        # 4. Act 4 Rough Edge Editor (15.5s)
        h4, del_t, key_ts = scene_act4_rough_edge_editor()
        events["act4_delete_time"] = del_t
        events["act4_key_times"] = key_ts
        render_html_to_mp4(browser, h4, 15.5, f"{OUT_DIR}/ui_act4_rough_edge_editor.mp4")

        # 5. Finale We Touch + Credits (9.5s)
        render_html_to_mp4(browser, scene_finale_we_touch(), 9.5, f"{OUT_DIR}/ui_finale_we_touch.mp4")

        browser.close()

    with open(f"{WORK_DIR}/ui_events.json", "w") as f:
        json.dump(events, f, indent=2)
    print("Saved UI sync events:", f"{WORK_DIR}/ui_events.json")


if __name__ == "__main__":
    main()
