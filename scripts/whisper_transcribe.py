#!/usr/bin/env python3
"""
CPU Whisper transcription pipeline for GitHub Actions.

Supported sources:
1) archive item (archive.org)
2) external URL (direct media URL or yt-dlp supported page URL)

Outputs transcript files and metadata into a run-specific folder.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, urlparse

import requests

ARCHIVE_METADATA = "https://archive.org/metadata"
ARCHIVE_DOWNLOAD = "https://archive.org/download"
VIDEO_AUDIO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".m4v",
    ".mkv",
    ".webm",
    ".mp3",
    ".m4a",
    ".aac",
    ".wav",
    ".flac",
    ".ogg",
}

ROOT_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = ROOT_DIR / "tmp" / "whisper"


def die(message: str, code: int = 1) -> None:
    print(message)
    sys.exit(code)


def env_str(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    return value if value else default


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha1_short(value: str, length: int = 12) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:length]


def write_step_output(name: str, value: str) -> None:
    output_file = env_str("GITHUB_OUTPUT", "")
    if not output_file:
        return
    with open(output_file, "a", encoding="utf-8") as fh:
        fh.write(f"{name}={value}\n")


def write_summary(lines: List[str]) -> None:
    summary_file = env_str("GITHUB_STEP_SUMMARY", "")
    if not summary_file:
        return
    with open(summary_file, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def run_command(command: List[str], fail_message: str) -> None:
    result = subprocess.run(command, text=True)
    if result.returncode != 0:
        die(fail_message)


def choose_archive_source(metadata: dict, preferred_filename: str) -> Optional[Tuple[str, int]]:
    files = metadata.get("files", [])
    if not isinstance(files, list):
        return None

    preferred_filename = preferred_filename.strip()
    if preferred_filename:
        for file_obj in files:
            if not isinstance(file_obj, dict):
                continue
            name = str(file_obj.get("name", "")).strip()
            if name == preferred_filename:
                size = int(str(file_obj.get("size", "0")).strip() or "0")
                return (name, max(0, size))

    candidates: List[Tuple[str, int]] = []
    for file_obj in files:
        if not isinstance(file_obj, dict):
            continue
        name = str(file_obj.get("name", "")).strip()
        lower = name.lower()
        suffix = Path(lower).suffix
        if suffix not in VIDEO_AUDIO_EXTENSIONS:
            continue
        if "thumb" in lower or "preview" in lower:
            continue
        try:
            size = int(str(file_obj.get("size", "0")).strip() or "0")
        except ValueError:
            size = 0
        if size > 0:
            candidates.append((name, size))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[1], reverse=True)
    return candidates[0]


def download_stream(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=300) as response:
        if response.status_code >= 400:
            die(f"Download failed ({response.status_code}) for {url}")
        with open(destination, "wb") as fh:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    fh.write(chunk)


def download_archive_source(identifier: str, preferred_filename: str, destination_dir: Path) -> Tuple[Path, str, str]:
    response = requests.get(f"{ARCHIVE_METADATA}/{identifier}", timeout=60)
    if response.status_code >= 400:
        die(f"Archive metadata failed ({response.status_code}) for {identifier}: {response.text}")

    metadata = response.json()
    if not isinstance(metadata, dict):
        die(f"Invalid archive metadata response for {identifier}")

    source = choose_archive_source(metadata, preferred_filename)
    if not source:
        die(f"No usable media file found in archive item {identifier}")

    filename, _ = source
    source_url = f"{ARCHIVE_DOWNLOAD}/{identifier}/{quote(filename, safe='/')}"
    ext = Path(filename).suffix or ".mp4"
    output_path = destination_dir / f"{identifier}{ext}"
    print(f"Downloading archive source: {source_url}")
    download_stream(source_url, output_path)
    return output_path, source_url, filename


def download_url_source(source_url: str, destination_dir: Path) -> Tuple[Path, str, str]:
    destination_dir.mkdir(parents=True, exist_ok=True)
    parsed = urlparse(source_url)
    ext = Path(parsed.path).suffix.lower()

    if ext in VIDEO_AUDIO_EXTENSIONS:
        output_path = destination_dir / f"url_{sha1_short(source_url, 14)}{ext}"
        print(f"Downloading direct URL source: {source_url}")
        download_stream(source_url, output_path)
        return output_path, source_url, output_path.name

    print(f"Downloading URL source via yt-dlp: {source_url}")
    template = str(destination_dir / ("url_" + sha1_short(source_url, 14) + ".%(ext)s"))
    command = [
        "yt-dlp",
        "--no-progress",
        "--no-warnings",
        "-f",
        "bv*+ba/b",
        "--merge-output-format",
        "mp4",
        "-o",
        template,
        source_url,
    ]
    run_command(command, f"yt-dlp failed for URL: {source_url}")

    candidates = sorted(destination_dir.glob("url_" + sha1_short(source_url, 14) + ".*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        die(f"yt-dlp did not produce any output file for URL: {source_url}")

    preferred = [path for path in candidates if path.suffix.lower() in VIDEO_AUDIO_EXTENSIONS]
    output_path = preferred[0] if preferred else candidates[0]
    return output_path, source_url, output_path.name


def seconds_to_srt_time(value: float) -> str:
    total_ms = int(max(0.0, value) * 1000)
    hours = total_ms // 3600000
    minutes = (total_ms % 3600000) // 60000
    seconds = (total_ms % 60000) // 1000
    millis = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def seconds_to_vtt_time(value: float) -> str:
    total_ms = int(max(0.0, value) * 1000)
    hours = total_ms // 3600000
    minutes = (total_ms % 3600000) // 60000
    seconds = (total_ms % 60000) // 1000
    millis = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


def trim_input_if_needed(source_path: Path, max_duration_seconds: int, work_dir: Path) -> Path:
    if max_duration_seconds <= 0:
        return source_path

    trimmed_path = work_dir / "trimmed_input.mp4"
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-t",
        str(max_duration_seconds),
        "-c",
        "copy",
        str(trimmed_path),
    ]
    result = subprocess.run(command, text=True)
    if result.returncode != 0 or not trimmed_path.exists():
        print("Trim failed, continuing with original source.")
        return source_path
    return trimmed_path


def transcribe_cpu(
    source_path: Path,
    *,
    model_name: str,
    language: str,
    task: str,
    compute_type: str,
) -> Dict[str, object]:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        die("Missing dependency faster-whisper. Install with: pip install faster-whisper")

    resolved_language = None if language == "auto" else language
    model = WhisperModel(model_name, device="cpu", compute_type=compute_type)
    segments_iter, info = model.transcribe(
        str(source_path),
        language=resolved_language,
        task=task,
        vad_filter=True,
    )

    segments: List[Dict[str, object]] = []
    for seg in segments_iter:
        text = str(getattr(seg, "text", "")).strip()
        if not text:
            continue
        segments.append(
            {
                "start": float(getattr(seg, "start", 0.0)),
                "end": float(getattr(seg, "end", 0.0)),
                "text": text,
            }
        )

    detected_language = str(getattr(info, "language", "") or "")
    duration = float(getattr(info, "duration", 0.0) or 0.0)
    language_probability = float(getattr(info, "language_probability", 0.0) or 0.0)
    return {
        "segments": segments,
        "detected_language": detected_language,
        "language_probability": language_probability,
        "duration_seconds": duration,
    }


def write_outputs(output_dir: Path, base_name: str, payload: Dict[str, object], output_format: str) -> Dict[str, Path]:
    segments = payload.get("segments", [])
    if not isinstance(segments, list):
        segments = []

    output_dir.mkdir(parents=True, exist_ok=True)
    format_value = output_format.strip().lower()
    write_all = format_value == "all"
    paths: Dict[str, Path] = {}

    if write_all or format_value == "txt":
        txt_path = output_dir / f"{base_name}.txt"
        txt_path.write_text("\n".join([str(seg.get("text", "")).strip() for seg in segments if str(seg.get("text", "")).strip()]), encoding="utf-8")
        paths["txt"] = txt_path

    if write_all or format_value == "srt":
        srt_path = output_dir / f"{base_name}.srt"
        lines: List[str] = []
        for idx, seg in enumerate(segments, start=1):
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", 0.0))
            text = str(seg.get("text", "")).strip()
            lines.extend([str(idx), f"{seconds_to_srt_time(start)} --> {seconds_to_srt_time(end)}", text, ""])
        srt_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        paths["srt"] = srt_path

    if write_all or format_value == "vtt":
        vtt_path = output_dir / f"{base_name}.vtt"
        lines = ["WEBVTT", ""]
        for seg in segments:
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", 0.0))
            text = str(seg.get("text", "")).strip()
            lines.extend([f"{seconds_to_vtt_time(start)} --> {seconds_to_vtt_time(end)}", text, ""])
        vtt_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        paths["vtt"] = vtt_path

    if write_all or format_value == "json":
        json_path = output_dir / f"{base_name}.json"
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        paths["json"] = json_path

    return paths


def main() -> None:
    os.chdir(ROOT_DIR)
    source_type = env_str("SOURCE_TYPE", "archive").lower()
    archive_identifier = env_str("ARCHIVE_IDENTIFIER", "")
    archive_filename = env_str("ARCHIVE_FILENAME", "")
    source_url_input = env_str("SOURCE_URL", "")
    whisper_model = env_str("WHISPER_MODEL", "base")
    whisper_language = env_str("WHISPER_LANGUAGE", "auto")
    whisper_task = env_str("WHISPER_TASK", "transcribe")
    compute_type = env_str("WHISPER_COMPUTE_TYPE", "int8")
    output_format = env_str("OUTPUT_FORMAT", "all")
    max_duration_seconds = env_int("MAX_DURATION_SECONDS", 0)
    run_key = env_str("WHISPER_RUN_KEY", "") or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    input_dir = TMP_DIR / "input"
    work_dir = TMP_DIR / "work"
    output_root = Path(env_str("WHISPER_OUTPUT_DIR", str(TMP_DIR / "output"))).resolve()
    output_dir = output_root / run_key
    input_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_path: Path
    resolved_source_url = ""
    resolved_source_name = ""

    if source_type == "archive":
        if not archive_identifier:
            die("ARCHIVE_IDENTIFIER is required when SOURCE_TYPE=archive")
        source_path, resolved_source_url, resolved_source_name = download_archive_source(
            archive_identifier,
            archive_filename,
            input_dir,
        )
    elif source_type == "url":
        if not source_url_input:
            die("SOURCE_URL is required when SOURCE_TYPE=url")
        source_path, resolved_source_url, resolved_source_name = download_url_source(
            source_url_input,
            input_dir,
        )
    else:
        die("Unsupported SOURCE_TYPE. Use archive or url.")

    transcription_source = trim_input_if_needed(source_path, max_duration_seconds, work_dir)
    print(f"Transcribing source: {transcription_source}")
    transcription = transcribe_cpu(
        transcription_source,
        model_name=whisper_model,
        language=whisper_language,
        task=whisper_task,
        compute_type=compute_type,
    )

    base_name = Path(resolved_source_name or source_path.name).stem or "transcript"
    transcript_paths = write_outputs(output_dir, base_name, transcription, output_format)

    metadata = {
        "created_at": now_iso(),
        "source_type": source_type,
        "source_path": str(source_path),
        "source_name": resolved_source_name,
        "source_url": resolved_source_url,
        "archive_identifier": archive_identifier,
        "whisper_model": whisper_model,
        "whisper_language_requested": whisper_language,
        "whisper_task": whisper_task,
        "compute_type": compute_type,
        "max_duration_seconds": max_duration_seconds,
        "detected_language": transcription.get("detected_language", ""),
        "language_probability": transcription.get("language_probability", 0.0),
        "duration_seconds": transcription.get("duration_seconds", 0.0),
        "segments_count": len(transcription.get("segments", [])),
        "transcript_files": {k: str(v) for k, v in transcript_paths.items()},
    }
    metadata_path = output_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    write_step_output("output_dir", str(output_dir))
    write_step_output("metadata_json", str(metadata_path))
    write_step_output("source_path", str(source_path))
    write_step_output("source_url", resolved_source_url)
    for key, value in transcript_paths.items():
        write_step_output(f"{key}_path", str(value))

    summary_lines = [
        "## Whisper CPU Transcription",
        f"- Source type: `{source_type}`",
        f"- Source url: `{resolved_source_url}`",
        f"- Model: `{whisper_model}`",
        f"- Task: `{whisper_task}`",
        f"- Language requested: `{whisper_language}`",
        f"- Language detected: `{metadata['detected_language']}`",
        f"- Segments: `{metadata['segments_count']}`",
        f"- Output dir: `{output_dir}`",
    ]
    write_summary(summary_lines)
    print("Transcription completed successfully.")
    print(json.dumps(metadata, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()

