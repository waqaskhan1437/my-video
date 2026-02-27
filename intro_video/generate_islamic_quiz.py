#!/usr/bin/env python3
"""
Islamic Quiz Video Generator - Urdu Voiceover
Vertical 9:16 format for YouTube Shorts / TikTok / Reels
Professional design with timer, engagement hooks, monetization-ready
"""

import asyncio
import json
import math
import os
import random
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import edge_tts

# ============================================================
# CONFIG
# ============================================================
W, H = 1080, 1920
FPS = 30
OUT = Path(__file__).parent / "islamic_quiz"
SCENES_D = OUT / "scenes"
AUDIO_D = OUT / "audio"
for d in [OUT, SCENES_D, AUDIO_D]:
    d.mkdir(exist_ok=True)

VOICE = "ur-PK-AsadNeural"  # Urdu male voice

# Fonts
FB = "C:/Windows/Fonts/arialbd.ttf"
FR = "C:/Windows/Fonts/arial.ttf"
FBK = "C:/Windows/Fonts/ariblk.ttf"

# Colors - Islamic green theme
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
BLUE_SOFT = (100, 150, 220)
DARK = (10, 10, 15)
TEAL = (30, 180, 170)


def font(size=48, bold=False, black=False):
    p = FBK if black else (FB if bold else FR)
    try:
        return ImageFont.truetype(p, size)
    except:
        return ImageFont.load_default()


# ============================================================
# ISLAMIC QUIZ QUESTIONS (Urdu)
# ============================================================
QUESTIONS = [
    {
        "id": "q01",
        "question": "Quran Majeed mein kitni Suratein hain?",
        "options": ["A) 112", "B) 114", "C) 116", "D) 120"],
        "correct": 1,  # B
        "answer_text": "Sahih Jawab hai B: Quran Majeed mein 114 Suratein hain!",
        "fun_fact": "Sabse chhoti Surah Al-Kausar hai aur sabse lambi Surah Al-Baqarah hai.",
        "voice_question": "Assalam-o-Alaikum! Aaj ka sawal hai: Quran Majeed mein kitni Suratein hain? Kya aap jante hain? Sochiye... das second mein jawab dein!",
        "voice_answer": "Waqt khatam! Sahih jawab hai: B, yaani Quran Majeed mein aik sau chaudah Suratein hain. Sabse chhoti Surah Al-Kausar hai aur sabse lambi Surah Al-Baqarah hai. Like karein aur share karein!",
        "timer": 10,
    },
    {
        "id": "q02",
        "question": "Islam mein kitne Kalme hain?",
        "options": ["A) 4", "B) 5", "C) 6", "D) 7"],
        "correct": 2,  # C
        "answer_text": "Sahih Jawab hai C: Islam mein 6 Kalme hain!",
        "fun_fact": "Pehla Kalma Tayyab hai aur Chhata Kalma Radd-e-Kufr hai.",
        "voice_question": "Doosra sawal! Islam mein kitne Kalme hain? Yeh bohat aasan sawal hai. Sochiye aur das second mein jawab dein!",
        "voice_answer": "Sahih jawab hai: C, yaani Islam mein chhe Kalme hain. Pehla Kalma Tayyab hai aur Chhata Kalma Radd e Kufr hai. Kya aapko sab Kalme yaad hain? Comment mein bataiye!",
        "timer": 10,
    },
    {
        "id": "q03",
        "question": "Pehli Wahi kis Ghaar mein nazil hui?",
        "options": ["A) Ghaar-e-Saur", "B) Ghaar-e-Hira", "C) Ghaar-e-Thawr", "D) Koh-e-Noor"],
        "correct": 1,  # B
        "answer_text": "Sahih Jawab hai B: Ghaar-e-Hira mein pehli Wahi nazil hui!",
        "fun_fact": "Pehli Wahi Surah Al-Alaq ki pehli 5 aayat theen: Iqra bismi Rabbik allazi khalaq.",
        "voice_question": "Teesra sawal! Pehli Wahi kis Ghaar mein nazil hui? Yeh bohat ahem sawal hai. Apna jawab sochiye... das second hain aapke paas!",
        "voice_answer": "Sahih jawab hai: B, yaani Pehli Wahi Ghaar e Hira mein nazil hui. Pehli Wahi Surah Al-Alaq ki pehli paanch aayat theen. Iqra bismi Rabbik allazi khalaq. Share karein taa ke dosray bhi seekhein!",
        "timer": 10,
    },
    {
        "id": "q04",
        "question": "Namaz din mein kitni dafa farz hai?",
        "options": ["A) 3 dafa", "B) 4 dafa", "C) 5 dafa", "D) 7 dafa"],
        "correct": 2,  # C
        "answer_text": "Sahih Jawab hai C: Din mein 5 waqt ki Namaz farz hai!",
        "fun_fact": "Fajr, Zuhr, Asr, Maghrib aur Isha - yeh paanch waqt ki namaz har Musalman par farz hai.",
        "voice_question": "Chautha sawal! Namaz din mein kitni dafa farz hai? Yeh har Musalman ko pata hona chahiye. Jawab dein das second mein!",
        "voice_answer": "Sahih jawab hai: C, yaani din mein paanch waqt ki Namaz farz hai. Fajr, Zuhr, Asr, Maghrib aur Isha. Allah humein paancho waqt ki namaz ki taufeeq de. Ameen! Follow karein mazeed sawaalat ke liye!",
        "timer": 10,
    },
    {
        "id": "q05",
        "question": "Islam ka pehla Rukn kaunsa hai?",
        "options": ["A) Namaz", "B) Roza", "C) Kalma Tayyab", "D) Hajj"],
        "correct": 2,  # C
        "answer_text": "Sahih Jawab hai C: Islam ka pehla Rukn Kalma Tayyab hai!",
        "fun_fact": "Islam ke 5 Rukn hain: Kalma, Namaz, Roza, Zakat aur Hajj.",
        "voice_question": "Aakhri sawal! Islam ka pehla Rukn kaunsa hai? Yeh bohat buniyadi sawal hai. Sochiye aur jawab dein... das second!",
        "voice_answer": "Sahih jawab hai: C, yaani Islam ka pehla Rukn Kalma Tayyab hai. La ilaha illallah Muhammad ur Rasool Allah. Islam ke paanch Rukn hain: Kalma, Namaz, Roza, Zakat aur Hajj. Shukriya dekhne ke liye! Like, Share aur Subscribe zaroor karein!",
        "timer": 10,
    },
]


# ============================================================
# DRAWING HELPERS
# ============================================================

def create_bg():
    """Create beautiful Islamic-themed background"""
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Subtle geometric Islamic pattern (diamond grid)
    for y in range(0, H, 80):
        for x in range(0, W, 80):
            draw.line([(x, y), (x + 40, y + 40)], fill=(15, 35, 20), width=1)
            draw.line([(x + 80, y), (x + 40, y + 40)], fill=(15, 35, 20), width=1)

    # Top decorative arch
    draw.arc([W // 2 - 250, -100, W // 2 + 250, 200], 0, 180, fill=GOLD, width=3)
    draw.arc([W // 2 - 240, -90, W // 2 + 240, 195], 0, 180, fill=GOLD_LIGHT, width=1)

    # Bottom gradient
    for y in range(H - 150, H):
        alpha = (y - (H - 150)) / 150
        c = int(8 + alpha * 10)
        draw.line([(0, y), (W, y)], fill=(c, c + 5, c))

    # Gold border lines top and bottom
    draw.rectangle([0, 0, W, 5], fill=GOLD)
    draw.rectangle([0, H - 5, W, H], fill=GOLD)

    return img


def draw_star(draw, cx, cy, r, color=GOLD, points=8):
    """Draw Islamic star pattern"""
    coords = []
    for i in range(points * 2):
        angle = math.radians(i * 360 / (points * 2) - 90)
        radius = r if i % 2 == 0 else r * 0.45
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        coords.append((x, y))
    draw.polygon(coords, fill=color)


def draw_crescent(draw, cx, cy, r, color=GOLD):
    """Draw crescent moon"""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    draw.ellipse([cx - r + 15, cy - r - 5, cx + r + 15, cy + r - 5], fill=BG_DARK)


def center_text(draw, text, y, f, fill=WHITE):
    bbox = draw.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), text, fill=fill, font=f)


def draw_timer_arc(draw, seconds_left, total, cx, cy, radius=60):
    """Draw countdown timer"""
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

    tf = font(48, black=True)
    num = str(max(0, int(seconds_left)))
    bbox = draw.textbbox((0, 0), num, font=tf)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw // 2, cy - 22), num, fill=arc_color, font=tf)


def draw_option_box(draw, text, x, y, w, h, state="normal", idx=0):
    """Draw an option box. state: normal, correct, wrong, selected"""
    colors_outline = [TEAL, BLUE_SOFT, GOLD, GREEN_LIGHT]

    if state == "correct":
        fill = (15, 80, 30)
        outline = GREEN_GLOW
        text_color = WHITE
    elif state == "wrong":
        fill = (80, 15, 15)
        outline = RED
        text_color = WHITE
    elif state == "selected":
        fill = (30, 30, 60)
        outline = GOLD
        text_color = GOLD
    else:
        fill = BG_CARD
        outline = colors_outline[idx % len(colors_outline)]
        text_color = CREAM

    draw.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=fill, outline=outline, width=3)

    # Option text
    tf = font(34, bold=True)
    bbox = draw.textbbox((0, 0), text, font=tf)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x + (w - tw) // 2, y + (h - th) // 2 - 2), text, fill=text_color, font=tf)


# ============================================================
# FRAME GENERATION
# ============================================================

def gen_quiz_frames(question, total_frames):
    """Generate all frames for one quiz question"""
    frames = []

    timer_sec = question["timer"]
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

    # Option box layout
    opt_w = W - 120
    opt_h = 90
    opt_gap = 25
    opt_x = 60
    opt_start_y = 900

    for fi in range(total_frames):
        img = create_bg()
        draw = ImageDraw.Draw(img)

        # Phase
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

        # === Top Section: Islamic decoration + Category ===

        # Crescent + Star
        draw_crescent(draw, 80, 80, 25, GOLD)
        draw_star(draw, W - 80, 80, 20, GOLD)

        # Category label
        cat_f = font(24, bold=True)
        center_text(draw, "ISLAMIC QUIZ", 40, cat_f, GOLD)

        # Decorative line
        draw.rectangle([100, 80, W - 100, 83], fill=GOLD)

        # === Question Box ===
        q_box_y = 130
        q_box_h = 250
        draw.rounded_rectangle([40, q_box_y, W - 40, q_box_y + q_box_h],
                               radius=20, fill=GREEN_DARK, outline=GOLD, width=2)

        # Small star decorations on question box
        draw_star(draw, 80, q_box_y + 30, 12, GOLD_LIGHT)
        draw_star(draw, W - 80, q_box_y + 30, 12, GOLD_LIGHT)

        # "SAWAL" label
        sf = font(22, bold=True)
        center_text(draw, "SAWAL", q_box_y + 15, sf, GOLD_LIGHT)

        # Question text - wrap if needed
        qf = font(38, bold=True)
        words = q_text.split()
        lines = []
        current = ""
        for word in words:
            test = current + " " + word if current else word
            bbox = draw.textbbox((0, 0), test, font=qf)
            if bbox[2] - bbox[0] > W - 140:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)

        q_y = q_box_y + 70
        for line in lines:
            center_text(draw, line, q_y, qf, CREAM)
            q_y += 55

        # === Question Number Badge ===
        qnum = question["id"].replace("q", "Q")
        draw.rounded_rectangle([W // 2 - 50, q_box_y - 25, W // 2 + 50, q_box_y + 10],
                               radius=15, fill=GOLD)
        nf = font(24, black=True)
        center_text(draw, qnum, q_box_y - 22, nf, BG_DARK)

        # === Options ===
        if phase == "intro":
            # Options appear with animation
            for idx, opt in enumerate(options):
                slide_progress = min(1.0, max(0, (pp - idx * 0.15) / 0.3))
                if slide_progress > 0:
                    oy = opt_start_y + idx * (opt_h + opt_gap)
                    offset_x = int((1 - slide_progress) * 200)
                    draw_option_box(draw, opt, opt_x + offset_x, oy, opt_w, opt_h, "normal", idx)

        elif phase == "timer":
            # All options visible, timer running
            for idx, opt in enumerate(options):
                oy = opt_start_y + idx * (opt_h + opt_gap)
                draw_option_box(draw, opt, opt_x, oy, opt_w, opt_h, "normal", idx)

            # Timer
            secs_left = timer_sec * (1 - pp)
            draw_timer_arc(draw, secs_left, timer_sec, W // 2, 700, 65)

            # Engagement text rotation
            eng_texts = [
                "Sochiye... Jawab kya hai?",
                "Comment mein bataiye!",
                "Kya aap jante hain?",
                "Video Pause karein aur sochein!",
            ]
            eng_idx = int(fi * 0.03) % len(eng_texts)
            ef = font(28, bold=True)
            center_text(draw, eng_texts[eng_idx], 800, ef, GOLD_LIGHT)

        elif phase == "reveal":
            # Flash correct answer
            for idx, opt in enumerate(options):
                oy = opt_start_y + idx * (opt_h + opt_gap)
                if idx == correct_idx:
                    # Correct answer flashes
                    if int(pp * 10) % 2 == 0:
                        draw_option_box(draw, opt, opt_x, oy, opt_w, opt_h, "correct", idx)
                    else:
                        draw_option_box(draw, opt + "  >>>", opt_x, oy, opt_w, opt_h, "correct", idx)
                else:
                    draw_option_box(draw, opt, opt_x, oy, opt_w, opt_h, "wrong", idx)

            # "SAHIH JAWAB" text
            center_text(draw, "SAHIH JAWAB!", 700, font(44, black=True), GREEN_GLOW)

            # Checkmark
            cx, cy = W // 2, 780
            draw.line([(cx - 20, cy), (cx - 5, cy + 20)], fill=GREEN_GLOW, width=5)
            draw.line([(cx - 5, cy + 20), (cx + 25, cy - 15)], fill=GREEN_GLOW, width=5)

        else:
            # Fact phase - show correct + fun fact
            for idx, opt in enumerate(options):
                oy = opt_start_y + idx * (opt_h + opt_gap)
                state = "correct" if idx == correct_idx else "wrong"
                draw_option_box(draw, opt, opt_x, oy, opt_w, opt_h, state, idx)

            # Fun fact box
            ff_y = opt_start_y + 4 * (opt_h + opt_gap) + 30
            draw.rounded_rectangle([50, ff_y, W - 50, ff_y + 140],
                                   radius=15, fill=(20, 35, 25), outline=TEAL, width=2)
            draw_star(draw, 85, ff_y + 20, 10, GOLD_LIGHT)
            ff_label = font(22, bold=True)
            draw.text((105, ff_y + 10), "Kya Aap Jante Hain?", fill=TEAL, font=ff_label)

            # Fact text wrapped
            fact = question["fun_fact"]
            ff = font(26)
            fact_words = fact.split()
            flines = []
            cur = ""
            for w in fact_words:
                test = cur + " " + w if cur else w
                bbox = draw.textbbox((0, 0), test, font=ff)
                if bbox[2] - bbox[0] > W - 160:
                    flines.append(cur)
                    cur = w
                else:
                    cur = test
            if cur:
                flines.append(cur)
            fy = ff_y + 45
            for fl in flines:
                draw.text((75, fy), fl, fill=CREAM, font=ff)
                fy += 35

        # === Bottom Section ===
        # Like/Share CTA
        if phase in ("timer", "fact"):
            cta_y = H - 180
            draw.rounded_rectangle([60, cta_y, W - 60, cta_y + 60],
                                   radius=30, fill=GREEN, outline=GOLD, width=2)
            ctf = font(26, bold=True)
            center_text(draw, "LIKE | SHARE | SUBSCRIBE", cta_y + 13, ctf, WHITE)

        # Channel name
        bf = font(20)
        center_text(draw, "Islamic Quiz - Roz Naya Sawal", H - 90, bf, GRAY)

        # Progress dots for question number
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
    """Generate Urdu voiceover for question + answer"""
    q_path = AUDIO_D / f"{question['id']}_q.mp3"
    comm = edge_tts.Communicate(question["voice_question"], VOICE, rate="+0%", pitch="-2Hz")
    sub = edge_tts.SubMaker()
    with open(str(q_path), "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            else:
                sub.feed(chunk)
    q_srt = AUDIO_D / f"{question['id']}_q.srt"
    with open(str(q_srt), "w", encoding="utf-8") as f:
        f.write(sub.get_srt())

    a_path = AUDIO_D / f"{question['id']}_a.mp3"
    comm2 = edge_tts.Communicate(question["voice_answer"], VOICE, rate="+0%", pitch="-2Hz")
    sub2 = edge_tts.SubMaker()
    with open(str(a_path), "wb") as f:
        async for chunk in comm2.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            else:
                sub2.feed(chunk)
    a_srt = AUDIO_D / f"{question['id']}_a.srt"
    with open(str(a_srt), "w", encoding="utf-8") as f:
        f.write(sub2.get_srt())

    return q_path, a_path


def get_dur(p):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "json", str(p)],
                       capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def frames_to_video(frame_list, video_path, audio_paths, timer_sec=10):
    """Combine frames with merged audio (question + silence + answer)"""
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
    print("  ISLAMIC QUIZ VIDEO GENERATOR - URDU")
    print("  YouTube Shorts / TikTok / Reels")
    print("=" * 55)

    all_videos = []

    for i, q in enumerate(QUESTIONS):
        print(f"\n--- Question {i+1}/{len(QUESTIONS)}: {q['id']} ---")

        print("  Generating Urdu voiceover...")
        q_audio, a_audio = await gen_audio(q)
        q_dur = get_dur(q_audio)
        a_dur = get_dur(a_audio)
        total_dur = q_dur + q["timer"] + a_dur + 3

        print(f"  Question: {q_dur:.1f}s, Timer: {q['timer']}s, Answer: {a_dur:.1f}s")
        print(f"  Generating {int(total_dur * FPS)} frames...")

        frame_list = gen_quiz_frames(q, int(total_dur * FPS))

        video_path = SCENES_D / f"{q['id']}.mp4"
        print("  Encoding video...")
        dur = frames_to_video(frame_list, video_path, [q_audio, a_audio], q["timer"])
        print(f"  Done: {video_path.name} ({dur:.1f}s)")
        all_videos.append(video_path)

    # Compilation
    print(f"\n=== Creating Compilation ===")
    concat_file = OUT / "all.txt"
    with open(str(concat_file), "w") as f:
        for vp in all_videos:
            f.write(f"file '{vp}'\n")

    compilation = OUT / "Islamic_Quiz_Compilation_Urdu.mp4"
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
    print(f"  COMPLETE in {elapsed:.0f} seconds!")
    print(f"")
    print(f"  Individual questions ({len(all_videos)} videos):")
    for vp in all_videos:
        d = get_dur(vp)
        s = vp.stat().st_size / (1024*1024)
        print(f"    {vp.name}: {d:.0f}s, {s:.1f}MB")
    print(f"")
    print(f"  Compilation: {compilation.name}")
    print(f"  Duration: {comp_dur:.0f}s | Size: {comp_size:.1f}MB")
    print(f"  Location: {compilation}")
    print(f"{'='*55}")


if __name__ == "__main__":
    asyncio.run(main())
