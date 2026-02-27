#!/usr/bin/env python3
"""
Islamic Quiz Video Generator - Full Urdu with Nastaleeq Font
Vertical 9:16 format for YouTube Shorts / TikTok / Reels
"""

import asyncio
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import edge_tts
import arabic_reshaper
from bidi.algorithm import get_display

# ============================================================
# CONFIG
# ============================================================
W, H = 1080, 1920
FPS = 30
OUT = Path(__file__).parent / "islamic_quiz_urdu"
SCENES_D = OUT / "scenes"
AUDIO_D = OUT / "audio"
for d in [OUT, SCENES_D, AUDIO_D]:
    d.mkdir(exist_ok=True)

VOICE = "ur-PK-UzmaNeural"  # Female - clearer Urdu voice

# Fonts - Nastaleeq
NASTALEEQ = "C:/Users/Salman Akbar/AppData/Local/Microsoft/Windows/Fonts/Jameel Noori Nastaleeq Kasheeda.ttf"
ARIAL_B = "C:/Windows/Fonts/arialbd.ttf"

# Colors
BG_DARK = (8, 20, 12)
BG_CARD = (15, 40, 25)
GOLD = (212, 175, 55)
GOLD_LIGHT = (245, 215, 110)
GREEN_DARK = (0, 80, 30)
GREEN = (16, 140, 60)
GREEN_LIGHT = (34, 197, 94)
GREEN_GLOW = (50, 220, 100)
WHITE = (255, 255, 255)
CREAM = (255, 248, 230)
GRAY = (160, 160, 160)
RED = (220, 50, 50)
TEAL = (30, 180, 170)
BLUE_SOFT = (100, 150, 220)


def urdu_font(size=48):
    try:
        return ImageFont.truetype(NASTALEEQ, size)
    except:
        return ImageFont.load_default()


def latin_font(size=48):
    try:
        return ImageFont.truetype(ARIAL_B, size)
    except:
        return ImageFont.load_default()


def shape_urdu(text):
    """Reshape and reorder Urdu text for correct RTL display"""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def center_urdu(draw, text, y, f, fill=WHITE):
    """Center Urdu text on screen"""
    display_text = shape_urdu(text)
    bbox = draw.textbbox((0, 0), display_text, font=f)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), display_text, fill=fill, font=f)


def center_latin(draw, text, y, f, fill=WHITE):
    bbox = draw.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), text, fill=fill, font=f)


# ============================================================
# QUESTIONS - Full Urdu Script
# ============================================================
QUESTIONS = [
    {
        "id": "q01",
        "question": "قرآن مجید میں کتنی سورتیں ہیں؟",
        "options": ["۱۱۲ )الف", "۱۱۴ )ب", "۱۱۶ )ج", "۱۲۰ )د"],
        "correct": 1,
        "answer_text": "صحیح جواب: قرآن مجید میں ۱۱۴ سورتیں ہیں",
        "fun_fact": "سب سے چھوٹی سورۃ الکوثر ہے اور سب سے بڑی سورۃ البقرۃ ہے",
        "voice_q": "السلام علیکم! آج کا سوال یہ ہے: قرآن مجید میں کتنی سورتیں ہیں؟ کیا آپ جانتے ہیں؟ سوچیے... دس سیکنڈ میں جواب دیں!",
        "voice_a": "وقت ختم! صحیح جواب ہے: ب، یعنی قرآن مجید میں ایک سو چودہ سورتیں ہیں۔ سب سے چھوٹی سورۃ الکوثر ہے اور سب سے بڑی سورۃ البقرۃ ہے۔ لائک کریں اور شیئر کریں!",
    },
    {
        "id": "q02",
        "question": "اسلام میں کتنے کلمے ہیں؟",
        "options": ["۴ )الف", "۵ )ب", "۶ )ج", "۷ )د"],
        "correct": 2,
        "answer_text": "صحیح جواب: اسلام میں ۶ کلمے ہیں",
        "fun_fact": "پہلا کلمہ طیب ہے اور چھٹا کلمہ ردِ کفر ہے",
        "voice_q": "دوسرا سوال! اسلام میں کتنے کلمے ہیں؟ یہ بہت آسان سوال ہے۔ سوچیے اور دس سیکنڈ میں جواب دیں!",
        "voice_a": "صحیح جواب ہے: ج، یعنی اسلام میں چھ کلمے ہیں۔ پہلا کلمہ طیب ہے اور چھٹا کلمہ ردِ کفر ہے۔ کیا آپ کو سب کلمے یاد ہیں؟ کمنٹ میں بتائیے!",
    },
    {
        "id": "q03",
        "question": "پہلی وحی کس غار میں نازل ہوئی؟",
        "options": ["غارِ ثور )الف", "غارِ حرا )ب", "کوہِ نور )ج", "کوہِ طور )د"],
        "correct": 1,
        "answer_text": "صحیح جواب: غارِ حرا میں پہلی وحی نازل ہوئی",
        "fun_fact": "پہلی وحی سورۃ العلق کی پہلی پانچ آیات تھیں: اقرأ باسم ربک الذی خلق",
        "voice_q": "تیسرا سوال! پہلی وحی کس غار میں نازل ہوئی؟ یہ بہت اہم سوال ہے۔ اپنا جواب سوچیے... دس سیکنڈ ہیں آپ کے پاس!",
        "voice_a": "صحیح جواب ہے: ب، یعنی پہلی وحی غارِ حرا میں نازل ہوئی۔ پہلی وحی سورۃ العلق کی پہلی پانچ آیات تھیں۔ شیئر کریں تاکہ دوسرے بھی سیکھیں!",
    },
    {
        "id": "q04",
        "question": "نماز دن میں کتنی بار فرض ہے؟",
        "options": ["۳ بار )الف", "۴ بار )ب", "۵ بار )ج", "۷ بار )د"],
        "correct": 2,
        "answer_text": "صحیح جواب: دن میں ۵ وقت کی نماز فرض ہے",
        "fun_fact": "فجر، ظہر، عصر، مغرب اور عشاء - یہ پانچ نمازیں ہر مسلمان پر فرض ہیں",
        "voice_q": "چوتھا سوال! نماز دن میں کتنی بار فرض ہے؟ یہ ہر مسلمان کو معلوم ہونا چاہیے۔ جواب دیں دس سیکنڈ میں!",
        "voice_a": "صحیح جواب ہے: ج، یعنی دن میں پانچ وقت کی نماز فرض ہے۔ فجر، ظہر، عصر، مغرب اور عشاء۔ اللہ ہمیں پانچوں وقت کی نماز کی توفیق دے۔ آمین!",
    },
    {
        "id": "q05",
        "question": "اسلام کا پہلا رکن کونسا ہے؟",
        "options": ["نماز )الف", "روزہ )ب", "کلمہ طیب )ج", "حج )د"],
        "correct": 2,
        "answer_text": "صحیح جواب: اسلام کا پہلا رکن کلمہ طیب ہے",
        "fun_fact": "اسلام کے ۵ ارکان ہیں: کلمہ، نماز، روزہ، زکوٰۃ اور حج",
        "voice_q": "آخری سوال! اسلام کا پہلا رکن کونسا ہے؟ یہ بنیادی سوال ہے۔ سوچیے اور جواب دیں... دس سیکنڈ!",
        "voice_a": "صحیح جواب ہے: ج، یعنی اسلام کا پہلا رکن کلمہ طیب ہے۔ لا الہ الا اللہ محمد الرسول اللہ۔ اسلام کے پانچ ارکان ہیں: کلمہ، نماز، روزہ، زکوٰۃ اور حج۔ شکریہ دیکھنے کا! لائک، شیئر اور سبسکرائب ضرور کریں!",
    },
]


# ============================================================
# DRAWING HELPERS
# ============================================================

def create_bg():
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)
    # Diamond grid pattern
    for y in range(0, H, 80):
        for x in range(0, W, 80):
            draw.line([(x, y), (x + 40, y + 40)], fill=(15, 35, 20), width=1)
            draw.line([(x + 80, y), (x + 40, y + 40)], fill=(15, 35, 20), width=1)
    # Top arch
    draw.arc([W // 2 - 250, -100, W // 2 + 250, 200], 0, 180, fill=GOLD, width=3)
    # Bottom gradient
    for y in range(H - 150, H):
        alpha = (y - (H - 150)) / 150
        c = int(8 + alpha * 10)
        draw.line([(0, y), (W, y)], fill=(c, c + 5, c))
    # Gold borders
    draw.rectangle([0, 0, W, 5], fill=GOLD)
    draw.rectangle([0, H - 5, W, H], fill=GOLD)
    return img


def draw_star(draw, cx, cy, r, color=GOLD, points=8):
    coords = []
    for i in range(points * 2):
        angle = math.radians(i * 360 / (points * 2) - 90)
        radius = r if i % 2 == 0 else r * 0.45
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        coords.append((x, y))
    draw.polygon(coords, fill=color)


def draw_crescent(draw, cx, cy, r, color=GOLD):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    draw.ellipse([cx - r + 15, cy - r - 5, cx + r + 15, cy + r - 5], fill=BG_DARK)


def draw_timer_arc(draw, seconds_left, total, cx, cy, radius=65):
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                 fill=(20, 20, 30), outline=GOLD, width=3)
    progress = max(0, seconds_left / total)
    if progress > 0.5:
        arc_color = GREEN_LIGHT
    elif progress > 0.2:
        arc_color = GOLD
    else:
        arc_color = RED
    start = -90
    end = start + int(360 * progress)
    if end > start:
        draw.arc([cx - radius + 5, cy - radius + 5, cx + radius - 5, cy + radius - 5],
                 start, end, fill=arc_color, width=8)
    tf = latin_font(48)
    num = str(max(0, int(seconds_left)))
    bbox = draw.textbbox((0, 0), num, font=tf)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw // 2, cy - 22), num, fill=arc_color, font=tf)


def draw_option_box(draw, text, x, y, w, h, state="normal", idx=0):
    colors_outline = [TEAL, BLUE_SOFT, GOLD, GREEN_LIGHT]
    if state == "correct":
        fill = (15, 80, 30)
        outline = GREEN_GLOW
        text_color = WHITE
    elif state == "wrong":
        fill = (80, 15, 15)
        outline = RED
        text_color = WHITE
    else:
        fill = BG_CARD
        outline = colors_outline[idx % len(colors_outline)]
        text_color = CREAM

    draw.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=fill, outline=outline, width=3)

    # Urdu option text
    f = urdu_font(38)
    display_text = shape_urdu(text)
    bbox = draw.textbbox((0, 0), display_text, font=f)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x + (w - tw) // 2, y + (h - th) // 2 - 8), display_text, fill=text_color, font=f)


# ============================================================
# FRAME GENERATION
# ============================================================

def gen_quiz_frames(question, total_frames):
    frames = []
    timer_sec = 10
    intro_f = int(2.5 * FPS)
    timer_f = timer_sec * FPS
    reveal_f = int(3.5 * FPS)
    fact_f = int(3 * FPS)
    needed = intro_f + timer_f + reveal_f + fact_f
    if total_frames < needed:
        total_frames = needed

    q_text = question["question"]
    options = question["options"]
    correct_idx = question["correct"]

    opt_w = W - 120
    opt_h = 100
    opt_gap = 25
    opt_x = 60
    opt_start_y = 920

    for fi in range(total_frames):
        img = create_bg()
        draw = ImageDraw.Draw(img)

        # Phase calc
        if fi < intro_f:
            phase = "intro"
            pp = fi / intro_f
        elif fi < intro_f + timer_f:
            phase = "timer"
            pp = (fi - intro_f) / timer_f
        elif fi < intro_f + timer_f + reveal_f:
            phase = "reveal"
            pp = (fi - intro_f - timer_f) / reveal_f
        else:
            phase = "fact"
            pp = (fi - intro_f - timer_f - reveal_f) / fact_f

        # === Top decoration ===
        draw_crescent(draw, 80, 80, 25, GOLD)
        draw_star(draw, W - 80, 80, 20, GOLD)

        # Title - Urdu
        title_f = urdu_font(36)
        center_urdu(draw, "اسلامی کوئز", 35, title_f, GOLD)

        # Decorative line
        draw.rectangle([100, 90, W - 100, 93], fill=GOLD)

        # === Question Box ===
        q_box_y = 140
        q_box_h = 280
        draw.rounded_rectangle([40, q_box_y, W - 40, q_box_y + q_box_h],
                               radius=20, fill=GREEN_DARK, outline=GOLD, width=2)

        draw_star(draw, 80, q_box_y + 30, 12, GOLD_LIGHT)
        draw_star(draw, W - 80, q_box_y + 30, 12, GOLD_LIGHT)

        # "سوال" label
        sf = urdu_font(28)
        center_urdu(draw, "سوال", q_box_y + 15, sf, GOLD_LIGHT)

        # Question number badge
        qnum = question["id"].replace("q0", "").replace("q", "")
        draw.rounded_rectangle([W // 2 - 40, q_box_y - 25, W // 2 + 40, q_box_y + 10],
                               radius=15, fill=GOLD)
        nf = latin_font(24)
        center_latin(draw, f"Q{qnum}", q_box_y - 22, nf, BG_DARK)

        # Question text - Urdu with wrapping
        qf = urdu_font(42)
        display_q = shape_urdu(q_text)
        # Simple wrap: try to fit, if too wide, split
        bbox = draw.textbbox((0, 0), display_q, font=qf)
        qw = bbox[2] - bbox[0]
        max_w = W - 140

        if qw <= max_w:
            q_lines = [display_q]
        else:
            # Split original text, reshape each part
            words = q_text.split()
            mid = len(words) // 2
            line1 = " ".join(words[:mid])
            line2 = " ".join(words[mid:])
            q_lines = [shape_urdu(line1), shape_urdu(line2)]

        q_y = q_box_y + 90
        for ql in q_lines:
            bbox = draw.textbbox((0, 0), ql, font=qf)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) // 2, q_y), ql, fill=CREAM, font=qf)
            q_y += 70

        # === Options ===
        if phase == "intro":
            for idx, opt in enumerate(options):
                slide_p = min(1.0, max(0, (pp - idx * 0.15) / 0.3))
                if slide_p > 0:
                    oy = opt_start_y + idx * (opt_h + opt_gap)
                    offset_x = int((1 - slide_p) * 200)
                    draw_option_box(draw, opt, opt_x + offset_x, oy, opt_w, opt_h, "normal", idx)

        elif phase == "timer":
            for idx, opt in enumerate(options):
                oy = opt_start_y + idx * (opt_h + opt_gap)
                draw_option_box(draw, opt, opt_x, oy, opt_w, opt_h, "normal", idx)
            # Timer
            secs_left = timer_sec * (1 - pp)
            draw_timer_arc(draw, secs_left, timer_sec, W // 2, 720, 65)

            # Engagement text - Urdu
            eng_texts = [
                "سوچیے... جواب کیا ہے؟",
                "کمنٹ میں بتائیے!",
                "کیا آپ جانتے ہیں؟",
                "ویڈیو روکیں اور سوچیں!",
            ]
            eng_idx = int(fi * 0.03) % len(eng_texts)
            ef = urdu_font(32)
            center_urdu(draw, eng_texts[eng_idx], 830, ef, GOLD_LIGHT)

        elif phase == "reveal":
            for idx, opt in enumerate(options):
                oy = opt_start_y + idx * (opt_h + opt_gap)
                if idx == correct_idx:
                    if int(pp * 10) % 2 == 0:
                        draw_option_box(draw, opt, opt_x, oy, opt_w, opt_h, "correct", idx)
                    else:
                        draw_option_box(draw, "✓  " + opt, opt_x, oy, opt_w, opt_h, "correct", idx)
                else:
                    draw_option_box(draw, opt, opt_x, oy, opt_w, opt_h, "wrong", idx)

            # "صحیح جواب"
            rf = urdu_font(48)
            center_urdu(draw, "صحیح جواب!", 720, rf, GREEN_GLOW)

            # Checkmark
            cx, cy = W // 2, 810
            draw.line([(cx - 20, cy), (cx - 5, cy + 20)], fill=GREEN_GLOW, width=5)
            draw.line([(cx - 5, cy + 20), (cx + 25, cy - 15)], fill=GREEN_GLOW, width=5)

        else:
            # Fact phase
            for idx, opt in enumerate(options):
                oy = opt_start_y + idx * (opt_h + opt_gap)
                state = "correct" if idx == correct_idx else "wrong"
                draw_option_box(draw, opt, opt_x, oy, opt_w, opt_h, state, idx)

            # Fun fact box
            ff_y = opt_start_y + 4 * (opt_h + opt_gap) + 30
            draw.rounded_rectangle([50, ff_y, W - 50, ff_y + 160],
                                   radius=15, fill=(20, 35, 25), outline=TEAL, width=2)
            draw_star(draw, 85, ff_y + 20, 10, GOLD_LIGHT)

            # "کیا آپ جانتے ہیں؟"
            ff_label = urdu_font(28)
            center_urdu(draw, "کیا آپ جانتے ہیں؟", ff_y + 10, ff_label, TEAL)

            # Fact text
            fact = question["fun_fact"]
            ff = urdu_font(30)
            display_fact = shape_urdu(fact)
            bbox = draw.textbbox((0, 0), display_fact, font=ff)
            fw = bbox[2] - bbox[0]
            if fw <= W - 160:
                fact_lines = [display_fact]
            else:
                words = fact.split()
                mid = len(words) // 2
                fact_lines = [shape_urdu(" ".join(words[:mid])), shape_urdu(" ".join(words[mid:]))]

            fy = ff_y + 60
            for fl in fact_lines:
                bbox = draw.textbbox((0, 0), fl, font=ff)
                tw = bbox[2] - bbox[0]
                draw.text(((W - tw) // 2, fy), fl, fill=CREAM, font=ff)
                fy += 45

        # === Bottom ===
        if phase in ("timer", "fact"):
            cta_y = H - 200
            draw.rounded_rectangle([60, cta_y, W - 60, cta_y + 65],
                                   radius=30, fill=GREEN, outline=GOLD, width=2)
            ctf = urdu_font(30)
            center_urdu(draw, "لائک | شیئر | سبسکرائب", cta_y + 8, ctf, WHITE)

        # Channel name
        bf = urdu_font(24)
        center_urdu(draw, "اسلامی کوئز - روز نیا سوال", H - 100, bf, GRAY)

        # Progress dots
        qnum_int = int(question["id"].replace("q", "")) - 1
        dot_y = H - 50
        total_q = len(QUESTIONS)
        dot_start = W // 2 - (total_q * 20) // 2
        for di in range(total_q):
            dx = dot_start + di * 20
            c = GOLD if di <= qnum_int else (50, 50, 50)
            draw.ellipse([dx, dot_y, dx + 10, dot_y + 10], fill=c)

        frames.append(np.array(img))

    return frames


# ============================================================
# AUDIO
# ============================================================
async def gen_audio(question):
    q_path = AUDIO_D / f"{question['id']}_q.mp3"
    comm = edge_tts.Communicate(question["voice_q"], VOICE, rate="-5%", pitch="-2Hz")
    sub = edge_tts.SubMaker()
    with open(str(q_path), "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            else:
                sub.feed(chunk)

    a_path = AUDIO_D / f"{question['id']}_a.mp3"
    comm2 = edge_tts.Communicate(question["voice_a"], VOICE, rate="-5%", pitch="-2Hz")
    sub2 = edge_tts.SubMaker()
    with open(str(a_path), "wb") as f:
        async for chunk in comm2.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            else:
                sub2.feed(chunk)

    return q_path, a_path


def get_dur(p):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "json", str(p)],
                       capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def frames_to_video(frame_list, video_path, audio_paths, timer_sec=10):
    merged = OUT / "temp_audio.mp3"
    silence = OUT / f"silence_{timer_sec}s.mp3"

    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono",
        "-t", str(timer_sec), "-c:a", "libmp3lame", "-b:a", "128k", str(silence)
    ], capture_output=True, check=True)

    concat_list = OUT / "ac.txt"
    with open(str(concat_list), "w") as f:
        f.write(f"file '{audio_paths[0]}'\n")
        f.write(f"file '{silence}'\n")
        f.write(f"file '{audio_paths[1]}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:a", "libmp3lame", "-b:a", "192k", str(merged)
    ], capture_output=True, check=True)

    total_dur = get_dur(merged)
    num_needed = int(total_dur * FPS)

    if len(frame_list) < num_needed:
        frame_list.extend([frame_list[-1]] * (num_needed - len(frame_list)))
    elif len(frame_list) > num_needed:
        frame_list = frame_list[:num_needed]

    tmp = OUT / "tmp_f"
    if tmp.exists():
        for old in tmp.glob("*.png"):
            old.unlink()
    tmp.mkdir(exist_ok=True)

    step = 3
    seq = 0
    saved = []
    for idx in range(0, len(frame_list), step):
        fp = tmp / f"f_{seq:06d}.png"
        Image.fromarray(frame_list[idx]).save(str(fp))
        saved.append(fp)
        seq += 1

    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(FPS // step),
        "-i", str(tmp / "f_%06d.png"),
        "-i", str(merged),
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-vf", f"fps={FPS}",
        "-pix_fmt", "yuv420p", "-shortest",
        str(video_path),
    ], capture_output=True, check=True)

    for fp in saved:
        fp.unlink(missing_ok=True)

    return total_dur


# ============================================================
# MAIN
# ============================================================
async def main():
    t0 = time.time()
    print("=" * 55)
    print("  ISLAMIC QUIZ - FULL URDU + NASTALEEQ FONT")
    print("=" * 55)

    all_videos = []

    for i, q in enumerate(QUESTIONS):
        print(f"\n--- Question {i+1}/{len(QUESTIONS)}: {q['id']} ---")

        print("  Generating Urdu voiceover...")
        q_audio, a_audio = await gen_audio(q)
        q_dur = get_dur(q_audio)
        a_dur = get_dur(a_audio)
        total_dur = q_dur + 10 + a_dur + 3

        print(f"  Q: {q_dur:.1f}s, Timer: 10s, A: {a_dur:.1f}s = {total_dur:.1f}s")
        print(f"  Generating {int(total_dur * FPS)} frames...")

        frame_list = gen_quiz_frames(q, int(total_dur * FPS))

        video_path = SCENES_D / f"{q['id']}.mp4"
        print("  Encoding video...")
        dur = frames_to_video(frame_list, video_path, [q_audio, a_audio], 10)
        print(f"  Done: {video_path.name} ({dur:.1f}s)")
        all_videos.append(video_path)

    # Compilation
    print(f"\n=== Creating Final Compilation ===")
    concat_file = OUT / "all.txt"
    with open(str(concat_file), "w") as f:
        for vp in all_videos:
            f.write(f"file '{vp}'\n")

    compilation = OUT / "Islamic_Quiz_Urdu_Nastaleeq.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(compilation),
    ], capture_output=True, check=True)

    comp_size = compilation.stat().st_size / (1024 * 1024)
    comp_dur = get_dur(compilation)

    elapsed = time.time() - t0
    print(f"\n{'='*55}")
    print(f"  COMPLETE in {elapsed:.0f}s!")
    print(f"  Videos: {len(all_videos)}")
    for vp in all_videos:
        d = get_dur(vp)
        s = vp.stat().st_size / (1024*1024)
        print(f"    {vp.name}: {d:.0f}s, {s:.1f}MB")
    print(f"  Compilation: {compilation.name}")
    print(f"  Duration: {comp_dur:.0f}s | Size: {comp_size:.1f}MB")
    print(f"  Location: {compilation}")
    print(f"{'='*55}")


if __name__ == "__main__":
    asyncio.run(main())
