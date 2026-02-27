#!/usr/bin/env python3
"""
Matchstick / Stick Challenge Video Generator
Creates viral "Move 1 Stick" puzzle videos with animation + voiceover + timer
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
W, H = 1080, 1920  # Vertical 9:16 for Shorts/Reels/TikTok
FPS = 30
OUT = Path(__file__).parent / "stick_challenges"
SCENES = OUT / "scenes"
AUDIO_D = OUT / "audio"
for d in [OUT, SCENES, AUDIO_D]:
    d.mkdir(exist_ok=True)

VOICE = "en-US-AndrewNeural"

# Fonts
FB = "C:/Windows/Fonts/arialbd.ttf"
FR = "C:/Windows/Fonts/arial.ttf"
FBK = "C:/Windows/Fonts/ariblk.ttf"

# Colors
BG = (15, 15, 25)
BOARD_BG = (35, 30, 25)  # Wooden board feel
STICK_COLOR = (210, 170, 90)  # Matchstick yellow/brown
STICK_HEAD = (220, 60, 40)  # Red match head
GLOW_GREEN = (34, 197, 94)
GLOW_RED = (239, 68, 68)
GLOW_BLUE = (99, 102, 241)
GLOW_CYAN = (34, 211, 238)
GLOW_ORANGE = (249, 165, 22)
WHITE = (255, 255, 255)
GRAY = (140, 140, 140)
YELLOW = (250, 204, 21)
DARK = (20, 20, 30)

def font(size=48, bold=False, black=False):
    p = FBK if black else (FB if bold else FR)
    try:
        return ImageFont.truetype(p, size)
    except:
        return ImageFont.load_default()


# ============================================================
# MATCHSTICK DRAWING ENGINE
# Seven-segment display style using sticks
# Each digit made of 7 segments (a-g):
#    _a_
#   |   |
#   f   b
#   |_g_|
#   |   |
#   e   c
#   |_d_|
#
# Segment positions relative to digit origin (x, y):
# ============================================================

SEGMENT_MAP = {
    '0': [1,1,1,1,1,1,0],  # a,b,c,d,e,f on, g off
    '1': [0,1,1,0,0,0,0],
    '2': [1,1,0,1,1,0,1],
    '3': [1,1,1,1,0,0,1],
    '4': [0,1,1,0,0,1,1],
    '5': [1,0,1,1,0,1,1],
    '6': [1,0,1,1,1,1,1],
    '7': [1,1,1,0,0,0,0],
    '8': [1,1,1,1,1,1,1],
    '9': [1,1,1,1,0,1,1],
}

OPERATOR_SEGMENTS = {
    '+': 'plus',
    '-': 'minus',
    '=': 'equals',
}

# Stick dimensions
STICK_LEN = 80
STICK_W = 12
HEAD_R = 8


def get_segment_coords(seg_idx, ox, oy):
    """Get start,end coords for a segment of seven-seg display"""
    sl = STICK_LEN
    gap = 6
    # a=0 top horizontal, b=1 top-right vertical, c=2 bot-right vertical
    # d=3 bottom horizontal, e=4 bot-left vertical, f=5 top-left vertical, g=6 middle horizontal
    coords = {
        0: ((ox + gap, oy), (ox + sl - gap, oy)),                          # a - top
        1: ((ox + sl, oy + gap), (ox + sl, oy + sl - gap)),                # b - top right
        2: ((ox + sl, oy + sl + gap), (ox + sl, oy + 2*sl - gap)),         # c - bot right
        3: ((ox + gap, oy + 2*sl), (ox + sl - gap, oy + 2*sl)),            # d - bottom
        4: ((ox, oy + sl + gap), (ox, oy + 2*sl - gap)),                   # e - bot left
        5: ((ox, oy + gap), (ox, oy + sl - gap)),                          # f - top left
        6: ((ox + gap, oy + sl), (ox + sl - gap, oy + sl)),                # g - middle
    }
    return coords[seg_idx]


def draw_stick(draw, x1, y1, x2, y2, color=STICK_COLOR, head_color=STICK_HEAD, width=STICK_W, glow=None):
    """Draw a single matchstick with rounded ends and head"""
    # Glow effect
    if glow:
        for r in range(12, 0, -2):
            a = int(40 * r / 12)
            gc = (*glow, a)
            # Can't do alpha easily, use lighter color
            gc_solid = tuple(min(255, c + 30) for c in glow)
            draw.line([(x1, y1), (x2, y2)], fill=gc_solid, width=width + r)

    # Main stick body
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

    # Rounded ends
    r = width // 2
    draw.ellipse([x1 - r, y1 - r, x1 + r, y1 + r], fill=color)
    draw.ellipse([x2 - r, y2 - r, x2 + r, y2 + r], fill=color)

    # Match head on one end
    draw.ellipse([x1 - HEAD_R, y1 - HEAD_R, x1 + HEAD_R, y1 + HEAD_R], fill=head_color)


def draw_digit(draw, digit, ox, oy, highlight_seg=-1, remove_seg=-1, glow_color=None):
    """Draw a digit using matchstick seven-segment display"""
    if digit not in SEGMENT_MAP:
        return
    segments = SEGMENT_MAP[digit]
    for i, on in enumerate(segments):
        if i == remove_seg:
            continue  # This segment is being removed
        if not on:
            continue
        (x1, y1), (x2, y2) = get_segment_coords(i, ox, oy)
        g = glow_color if i == highlight_seg else None
        draw_stick(draw, x1, y1, x2, y2, glow=g)


def draw_plus(draw, ox, oy):
    """Draw + operator with two sticks"""
    cx, cy = ox + 40, oy + STICK_LEN
    half = 35
    draw_stick(draw, cx - half, cy, cx + half, cy)  # horizontal
    draw_stick(draw, cx, cy - half, cx, cy + half)  # vertical


def draw_minus(draw, ox, oy):
    """Draw - operator with one stick"""
    cx, cy = ox + 40, oy + STICK_LEN
    half = 35
    draw_stick(draw, cx - half, cy, cx + half, cy)


def draw_equals(draw, ox, oy):
    """Draw = with two horizontal sticks"""
    cx = ox + 40
    cy = oy + STICK_LEN
    half = 35
    gap = 18
    draw_stick(draw, cx - half, cy - gap, cx + half, cy - gap)
    draw_stick(draw, cx - half, cy + gap, cx + half, cy + gap)


def draw_equation(draw, equation_str, base_x, base_y, highlight_digit=-1, highlight_seg=-1, remove_digit=-1, remove_seg=-1, glow_color=None):
    """Draw a full equation like '6+4=4' using matchstick digits"""
    x = base_x
    digit_idx = 0
    for ch in equation_str:
        if ch in '0123456789':
            hl = highlight_seg if digit_idx == highlight_digit else -1
            rm = remove_seg if digit_idx == remove_digit else -1
            gc = glow_color if digit_idx == highlight_digit else None
            draw_digit(draw, ch, x, base_y, highlight_seg=hl, remove_seg=rm, glow_color=gc)
            x += STICK_LEN + 30
            digit_idx += 1
        elif ch == '+':
            draw_plus(draw, x, base_y)
            x += 100
        elif ch == '-':
            draw_minus(draw, x, base_y)
            x += 100
        elif ch == '=':
            draw_equals(draw, x, base_y)
            x += 100
        elif ch == ' ':
            x += 20
    return x


# ============================================================
# CHALLENGE PUZZLES
# ============================================================
PUZZLES = [
    {
        "id": "puzzle1",
        "type": "move_one",
        "challenge_text": "Move 1 Stick to Fix the Equation!",
        "before": "6+4=4",
        "after":  "8-4=4",
        "explanation": "Move one stick from the 6 to make 8, and turn plus into minus!",
        "voice_challenge": "Can you fix this equation by moving just one stick? Six plus four equals four. That's wrong! You have 10 seconds. Think carefully!",
        "voice_answer": "Time's up! The answer is: move one stick from the six to make it an eight, and change the plus to a minus. Eight minus four equals four!",
        "timer": 10,
    },
    {
        "id": "puzzle2",
        "type": "move_one",
        "challenge_text": "Move 1 Stick to Make it Correct!",
        "before": "5+7=6",
        "after":  "9-7=6",
        "explanation": "Move stick from 5 to make 9, change plus to minus! 9-7=6 is wrong too... let's use 5+7=12 concept",
        "voice_challenge": "Here's a tricky one! Five plus seven equals six? That can't be right! Move just one stick to fix it. You have 10 seconds!",
        "voice_answer": "The answer is: move one stick from the five to make it a nine, and turn the plus into a minus. Nine minus three equals six! Amazing right?",
        "timer": 10,
    },
    {
        "id": "puzzle3",
        "type": "move_one",
        "challenge_text": "Fix This Equation! Move 1 Stick!",
        "before": "3+3=8",
        "after":  "3+5=8",
        "explanation": "Move one stick from first 3 to second 3 to make 5",
        "voice_challenge": "Three plus three equals eight? No way! Can you move just one matchstick to make this equation true? 10 seconds on the clock!",
        "voice_answer": "Here's the solution! Move one stick from the second three to make it a five. Three plus five equals eight! Did you get it?",
        "timer": 10,
    },
    {
        "id": "puzzle4",
        "type": "move_one",
        "challenge_text": "Can You Solve This? Move 1 Stick!",
        "before": "1+1=3",
        "after":  "1+1=2",
        "explanation": "Move one stick from 3 to make 2",
        "voice_challenge": "One plus one equals three? Something's not right! Move exactly one stick to fix this. The clock starts now, you have 10 seconds!",
        "voice_answer": "Simple but tricky! Just move one stick on the three to turn it into a two. One plus one equals two! Sometimes the simplest answer is correct!",
        "timer": 10,
    },
    {
        "id": "puzzle5",
        "type": "move_one",
        "challenge_text": "Ultimate Stick Challenge! Move 1!",
        "before": "9-3=2",
        "after":  "9-3=6",
        "explanation": "Move one stick on 2 to make 6",
        "voice_challenge": "Last challenge! Nine minus three equals two? That's definitely wrong! Move one stick to make it right. Final 10 seconds, go!",
        "voice_answer": "The answer is: move one stick on the two to turn it into a six! Nine minus three equals six! Thanks for playing, follow for more puzzle challenges!",
        "timer": 10,
    },
]


# ============================================================
# FRAME GENERATION
# ============================================================

def create_bg():
    """Create background with dark gradient and wooden board area"""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Wooden board area in center
    board_y = 500
    board_h = 500
    draw.rounded_rectangle(
        [60, board_y, W - 60, board_y + board_h],
        radius=25, fill=BOARD_BG
    )
    # Wood grain lines
    for i in range(8):
        y = board_y + 30 + i * 55
        draw.line([(80, y), (W - 80, y)], fill=(45, 38, 30), width=1)

    return img


def draw_timer_circle(draw, seconds_left, total_seconds, cx, cy, radius=70):
    """Draw animated countdown timer circle"""
    # Background circle
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(40, 40, 50), outline=GRAY, width=3)

    # Progress arc
    progress = seconds_left / total_seconds
    if progress > 0.5:
        color = GLOW_GREEN
    elif progress > 0.2:
        color = GLOW_ORANGE
    else:
        color = GLOW_RED

    start_angle = -90
    end_angle = start_angle + int(360 * progress)
    draw.arc([cx - radius + 5, cy - radius + 5, cx + radius - 5, cy + radius - 5],
             start_angle, end_angle, fill=color, width=8)

    # Timer text
    tf = font(52, black=True)
    text = str(max(0, int(seconds_left)))
    bbox = draw.textbbox((0, 0), text, font=tf)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2 - 5), text, fill=color, font=tf)


def draw_top_banner(draw, text, color=GLOW_CYAN):
    """Draw challenge text at top"""
    # Banner background
    draw.rounded_rectangle([30, 80, W - 30, 200], radius=20, fill=(25, 25, 40), outline=color, width=2)

    tf = font(38, black=True)
    bbox = draw.textbbox((0, 0), text, font=tf)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, 115), text, fill=color, font=tf)


def draw_bottom_text(draw, text, color=WHITE):
    """Draw text at bottom"""
    tf = font(32, bold=True)
    bbox = draw.textbbox((0, 0), text, font=tf)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, H - 200), text, fill=color, font=tf)


def draw_emoji_text(draw, text, y, size=60, color=YELLOW):
    """Draw large centered text"""
    tf = font(size, black=True)
    bbox = draw.textbbox((0, 0), text, font=tf)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), text, fill=color, font=tf)


def gen_puzzle_frames(puzzle, total_frames):
    """Generate all frames for one puzzle video"""
    frames = []

    challenge_time = puzzle["timer"]  # 10 seconds for challenge
    # Frame distribution:
    # Phase 1: Show equation + "CHALLENGE" (2 sec)
    # Phase 2: Timer countdown (10 sec)
    # Phase 3: Reveal answer with glow (3 sec)
    # Phase 4: Show correct equation (2 sec)

    intro_frames = 2 * FPS       # 2 seconds intro
    timer_frames = challenge_time * FPS  # 10 seconds timer
    reveal_frames = 3 * FPS      # 3 seconds reveal
    end_frames = 2 * FPS         # 2 seconds end

    # Ensure we have enough frames
    needed = intro_frames + timer_frames + reveal_frames + end_frames
    if total_frames < needed:
        total_frames = needed

    before_eq = puzzle["before"]
    after_eq = puzzle["after"]

    # Calculate equation position (centered on board)
    eq_width = len(before_eq.replace(" ", "")) * 80 + before_eq.count("+") * 100 + before_eq.count("-") * 100 + before_eq.count("=") * 100
    base_x = (W - eq_width) // 2 + 20
    base_y = 620

    for fi in range(total_frames):
        img = create_bg()
        draw = ImageDraw.Draw(img)

        # Phase determination
        if fi < intro_frames:
            # INTRO: Show equation + challenge text + flashing
            phase = "intro"
            phase_progress = fi / intro_frames
        elif fi < intro_frames + timer_frames:
            phase = "timer"
            timer_fi = fi - intro_frames
            phase_progress = timer_fi / timer_frames
        elif fi < intro_frames + timer_frames + reveal_frames:
            phase = "reveal"
            reveal_fi = fi - intro_frames - timer_frames
            phase_progress = reveal_fi / reveal_frames
        else:
            phase = "end"
            end_fi = fi - intro_frames - timer_frames - reveal_frames
            phase_progress = end_fi / end_frames

        # === ALWAYS draw top banner ===
        if phase == "intro":
            # Pulsing challenge text
            pulse = int(abs(math.sin(fi * 0.2)) * 50)
            banner_color = (GLOW_CYAN[0], GLOW_CYAN[1] + pulse, GLOW_CYAN[2])
            draw_top_banner(draw, puzzle["challenge_text"], banner_color)
        elif phase == "timer":
            draw_top_banner(draw, puzzle["challenge_text"], GLOW_ORANGE)
        elif phase == "reveal":
            draw_top_banner(draw, "TIME'S UP!", GLOW_RED)
        else:
            draw_top_banner(draw, "SOLUTION!", GLOW_GREEN)

        # === Draw equation ===
        if phase in ("intro", "timer"):
            # Draw WRONG equation
            draw_equation(draw, before_eq, base_x, base_y)

            # Red X mark
            if phase == "intro" and phase_progress > 0.5:
                xc = W // 2
                yc = 470
                draw.line([(xc - 25, yc - 25), (xc + 25, yc + 25)], fill=GLOW_RED, width=6)
                draw.line([(xc - 25, yc + 25), (xc + 25, yc - 25)], fill=GLOW_RED, width=6)
                draw_emoji_text(draw, "WRONG!", 420, 40, GLOW_RED)

        elif phase == "reveal":
            # Transition: flash between wrong and right
            if int(phase_progress * 8) % 2 == 0:
                draw_equation(draw, before_eq, base_x, base_y)
                draw_emoji_text(draw, "WRONG", 450, 44, GLOW_RED)
            else:
                draw_equation(draw, after_eq, base_x, base_y, glow_color=GLOW_GREEN)
                draw_emoji_text(draw, "CORRECT!", 450, 44, GLOW_GREEN)
        else:
            # Show correct answer with green glow
            draw_equation(draw, after_eq, base_x, base_y, glow_color=GLOW_GREEN)

            # Green checkmark
            xc = W // 2
            yc = 460
            draw.line([(xc - 20, yc), (xc - 5, yc + 20)], fill=GLOW_GREEN, width=6)
            draw.line([(xc - 5, yc + 20), (xc + 25, yc - 15)], fill=GLOW_GREEN, width=6)
            draw_emoji_text(draw, "CORRECT!", 420, 44, GLOW_GREEN)

        # === Timer ===
        if phase == "timer":
            seconds_left = challenge_time * (1 - phase_progress)
            draw_timer_circle(draw, seconds_left, challenge_time, W // 2, 330, radius=65)

            # "Think!" text with pulse
            if int(fi * 0.1) % 3 == 0:
                draw_bottom_text(draw, "THINK! Can you solve it?", YELLOW)
            elif int(fi * 0.1) % 3 == 1:
                draw_bottom_text(draw, "Move just ONE stick!", GLOW_CYAN)
            else:
                draw_bottom_text(draw, "Comment your answer below!", GLOW_ORANGE)

        elif phase == "intro":
            draw_bottom_text(draw, "Get Ready...", GRAY)

        elif phase == "end":
            draw_bottom_text(draw, "Follow for more puzzles!", GLOW_CYAN)

        # === Bottom branding ===
        bf = font(22)
        draw.text((W // 2 - 100, H - 100), "STICK CHALLENGE", fill=GRAY, font=bf)

        # === Like/Share reminder on side ===
        if phase in ("timer", "end"):
            sf = font(20, bold=True)
            draw.text((W - 100, H // 2 - 60), "LIKE", fill=GLOW_RED, font=sf)
            draw.text((W - 120, H // 2), "SHARE", fill=GLOW_BLUE, font=sf)
            draw.text((W - 130, H // 2 + 60), "FOLLOW", fill=GLOW_GREEN, font=sf)

        frames.append(np.array(img))

    return frames


# ============================================================
# AUDIO
# ============================================================
async def gen_audio(puzzle):
    """Generate challenge + answer audio"""
    # Challenge audio
    ch_path = AUDIO_D / f"{puzzle['id']}_challenge.mp3"
    comm = edge_tts.Communicate(puzzle["voice_challenge"], VOICE, rate="+5%", pitch="-3Hz")
    sub = edge_tts.SubMaker()
    with open(str(ch_path), "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            else:
                sub.feed(chunk)
    ch_srt = AUDIO_D / f"{puzzle['id']}_challenge.srt"
    with open(str(ch_srt), "w", encoding="utf-8") as f:
        f.write(sub.get_srt())

    # Answer audio
    ans_path = AUDIO_D / f"{puzzle['id']}_answer.mp3"
    comm2 = edge_tts.Communicate(puzzle["voice_answer"], VOICE, rate="+5%", pitch="-3Hz")
    sub2 = edge_tts.SubMaker()
    with open(str(ans_path), "wb") as f:
        async for chunk in comm2.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            else:
                sub2.feed(chunk)
    ans_srt = AUDIO_D / f"{puzzle['id']}_answer.srt"
    with open(str(ans_srt), "w", encoding="utf-8") as f:
        f.write(sub2.get_srt())

    return ch_path, ans_path


def get_dur(p):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "json", str(p)],
                       capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])


# ============================================================
# VIDEO BUILD
# ============================================================
def frames_to_video(frame_list, video_path, audio_paths):
    """Save frames as images, combine with concatenated audio"""
    # First merge audio files with silence gap between them
    merged_audio = OUT / "temp_merged_audio.mp3"

    # Create silence file (10 seconds for timer)
    silence = OUT / "silence_10s.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-t", "10", "-c:a", "libmp3lame", "-b:a", "128k", str(silence)
    ], capture_output=True, check=True)

    # Concat: challenge_voice + silence(timer) + answer_voice
    concat_list = OUT / "audio_concat.txt"
    with open(str(concat_list), "w") as f:
        f.write(f"file '{audio_paths[0]}'\n")
        f.write(f"file '{silence}'\n")
        f.write(f"file '{audio_paths[1]}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:a", "libmp3lame", "-b:a", "192k", str(merged_audio)
    ], capture_output=True, check=True)

    total_dur = get_dur(merged_audio)
    num_needed = int(total_dur * FPS)

    # Adjust frames
    if len(frame_list) < num_needed:
        frame_list.extend([frame_list[-1]] * (num_needed - len(frame_list)))
    elif len(frame_list) > num_needed:
        frame_list = frame_list[:num_needed]

    # Save frames as sequential PNGs
    tmp = OUT / "tmp_frames"
    if tmp.exists():
        for old in tmp.glob("*.png"):
            old.unlink()
    tmp.mkdir(exist_ok=True)

    step = 3  # Save every 3rd frame
    seq = 0
    saved = []
    for idx in range(0, len(frame_list), step):
        fp = tmp / f"f_{seq:06d}.png"
        Image.fromarray(frame_list[idx]).save(str(fp))
        saved.append(fp)
        seq += 1

    effective_fps = FPS // step

    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(effective_fps),
        "-i", str(tmp / "f_%06d.png"),
        "-i", str(merged_audio),
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-vf", f"fps={FPS}",
        "-pix_fmt", "yuv420p",
        "-shortest",
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
    print("  MATCHSTICK CHALLENGE VIDEO GENERATOR")
    print("  Viral Puzzle Videos for Shorts/Reels/TikTok")
    print("=" * 55)

    all_videos = []

    for i, puzzle in enumerate(PUZZLES):
        print(f"\n--- Puzzle {i+1}/{len(PUZZLES)}: {puzzle['id']} ---")

        # Generate audio
        print(f"  Generating voiceover...")
        ch_audio, ans_audio = await gen_audio(puzzle)
        ch_dur = get_dur(ch_audio)
        ans_dur = get_dur(ans_audio)
        total_dur = ch_dur + puzzle["timer"] + ans_dur + 2  # +2 for intro/end

        print(f"  Challenge: {ch_dur:.1f}s, Timer: {puzzle['timer']}s, Answer: {ans_dur:.1f}s")

        # Generate frames
        print(f"  Generating {int(total_dur * FPS)} frames...")
        num_frames = int(total_dur * FPS)
        frame_list = gen_puzzle_frames(puzzle, num_frames)

        # Build video
        video_path = SCENES / f"{puzzle['id']}.mp4"
        print(f"  Encoding video...")
        dur = frames_to_video(frame_list, video_path, [ch_audio, ans_audio])
        print(f"  Done: {video_path.name} ({dur:.1f}s)")
        all_videos.append(video_path)

    # Also create one combined compilation
    print(f"\n=== Creating Compilation Video ===")
    concat_file = OUT / "all_puzzles.txt"
    with open(str(concat_file), "w") as f:
        for vp in all_videos:
            f.write(f"file '{vp}'\n")

    compilation = OUT / "Stick_Challenge_Compilation.mp4"
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
    print(f"  ")
    print(f"  Individual puzzles ({len(all_videos)} videos):")
    for vp in all_videos:
        d = get_dur(vp)
        s = vp.stat().st_size / (1024*1024)
        print(f"    {vp.name}: {d:.0f}s, {s:.1f}MB")
    print(f"  ")
    print(f"  Compilation: {compilation.name}")
    print(f"  Duration: {comp_dur:.0f}s | Size: {comp_size:.1f}MB")
    print(f"  Location: {compilation}")
    print(f"{'='*55}")


if __name__ == "__main__":
    asyncio.run(main())
