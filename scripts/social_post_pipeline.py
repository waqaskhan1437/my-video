#!/usr/bin/env python3
"""
Archive.org -> YouTube automation.

For each new Archive item with a given identifier prefix:
1. Download source video from archive.org
2. Build full horizontal video (16:9)
3. Build short vertical video (9:16, <=59s)
4. Upload both to YouTube
5. Store progress in social_state.json
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

ARCHIVE_ADVANCEDSEARCH = "https://archive.org/advancedsearch.php"
ARCHIVE_METADATA = "https://archive.org/metadata"
ARCHIVE_DOWNLOAD = "https://archive.org/download"
YT_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

ROOT_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = ROOT_DIR / "tmp" / "social"
STATE_FILE = ROOT_DIR / "social_state.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def die(message: str, code: int = 1) -> None:
    print(message)
    sys.exit(code)


def env_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        die(f"Missing required env var: {name}")
    return value


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        parsed = int(raw)
        return parsed if parsed > 0 else default
    except ValueError:
        return default


def write_summary(lines: List[str]) -> None:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY", "").strip()
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def load_state() -> Dict[str, dict]:
    if not STATE_FILE.exists():
        return {}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return {}


def save_state(state: Dict[str, dict]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def archive_search(prefix: str, max_scan: int = 300) -> List[str]:
    identifiers: List[str] = []
    page = 1
    rows = 100
    query = f"identifier:{prefix}* AND mediatype:movies"

    while len(identifiers) < max_scan:
        params = {
            "q": query,
            "fl[]": "identifier",
            "sort[]": "publicdate asc",
            "rows": str(rows),
            "page": str(page),
            "output": "json",
        }
        response = requests.get(ARCHIVE_ADVANCEDSEARCH, params=params, timeout=60)
        if response.status_code >= 400:
            die(f"Archive search failed ({response.status_code}): {response.text}")
        payload = response.json()
        docs = payload.get("response", {}).get("docs", [])
        if not docs:
            break
        for doc in docs:
            item_id = str(doc.get("identifier", "")).strip()
            if item_id:
                identifiers.append(item_id)
                if len(identifiers) >= max_scan:
                    break
        page += 1

    # Unique while preserving order
    seen = set()
    output: List[str] = []
    for item_id in identifiers:
        if item_id in seen:
            continue
        seen.add(item_id)
        output.append(item_id)
    return output


def fetch_archive_metadata(identifier: str) -> dict:
    response = requests.get(f"{ARCHIVE_METADATA}/{identifier}", timeout=60)
    if response.status_code >= 400:
        die(f"Failed metadata for {identifier} ({response.status_code}): {response.text}")
    return response.json()


def choose_source_file(metadata: dict) -> Optional[Tuple[str, int]]:
    candidates: List[Tuple[str, int]] = []
    for file_obj in metadata.get("files", []):
        name = str(file_obj.get("name", ""))
        lower_name = name.lower()
        if not lower_name.endswith(".mp4"):
            continue
        if "thumb" in lower_name or "preview" in lower_name:
            continue
        size_raw = str(file_obj.get("size", "0")).strip()
        try:
            size = int(size_raw)
        except ValueError:
            size = 0
        if size <= 0:
            continue
        candidates.append((name, size))
    if not candidates:
        return None
    # Pick largest mp4 to avoid tiny derivatives.
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0]


def download_archive_file(identifier: str, filename: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded_name = quote(filename, safe="/")
    url = f"{ARCHIVE_DOWNLOAD}/{identifier}/{encoded_name}"
    print(f"Downloading source: {url}")
    with requests.get(url, stream=True, timeout=120) as response:
        if response.status_code >= 400:
            die(f"Download failed ({response.status_code}) for {url}")
        with open(destination, "wb") as fh:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    fh.write(chunk)


def run_command(command: List[str], fail_message: str) -> None:
    result = subprocess.run(command, text=True)
    if result.returncode != 0:
        die(fail_message)


def make_full_horizontal(source: Path, output_file: Path) -> None:
    # Convert to 16:9 with safe padding for consistent horizontal upload.
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-vf",
        "scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(output_file),
    ]
    run_command(command, "ffmpeg full-video conversion failed.")


def make_vertical_short(source: Path, output_file: Path) -> None:
    # Build Shorts-compatible output: 9:16 and <=59 seconds.
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-t",
        "59",
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "24",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        "-movflags",
        "+faststart",
        str(output_file),
    ]
    run_command(command, "ffmpeg short-video conversion failed.")


def get_youtube_client() -> object:
    creds = Credentials(
        token=None,
        refresh_token=env_required("YT_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=env_required("YT_CLIENT_ID"),
        client_secret=env_required("YT_CLIENT_SECRET"),
        scopes=[YT_UPLOAD_SCOPE],
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def shorten_title(text: str, max_len: int = 95) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 3].rstrip() + "..."


def upload_youtube_video(
    youtube,
    file_path: Path,
    *,
    title: str,
    description: str,
    privacy_status: str,
) -> str:
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(str(file_path), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        _, response = request.next_chunk()

    video_id = response.get("id", "").strip()
    if not video_id:
        die("YouTube upload returned no video id.")
    return video_id


def process_identifier(
    *,
    identifier: str,
    metadata: dict,
    state: Dict[str, dict],
    youtube,
    privacy_status: str,
) -> Tuple[bool, List[str]]:
    updated = False
    messages: List[str] = []

    record = state.get(identifier, {})
    full_done = bool(record.get("full_video_id"))
    short_done = bool(record.get("short_video_id"))
    if full_done and short_done:
        messages.append(f"- `{identifier}` already complete, skipped.")
        return updated, messages

    source_choice = choose_source_file(metadata)
    if not source_choice:
        messages.append(f"- `{identifier}` skipped: no usable mp4 file.")
        return updated, messages

    source_name, source_size = source_choice
    base_title = str(metadata.get("metadata", {}).get("title", identifier)).strip() or identifier
    archive_url = f"https://archive.org/details/{identifier}"

    work_dir = TMP_DIR / identifier
    work_dir.mkdir(parents=True, exist_ok=True)
    source_path = work_dir / "source.mp4"
    full_path = work_dir / "full.mp4"
    short_path = work_dir / "short.mp4"

    download_archive_file(identifier, source_name, source_path)

    if not full_done:
        print(f"Creating full video: {identifier}")
        make_full_horizontal(source_path, full_path)
        full_title = shorten_title(f"{base_title} | Full Video")
        full_desc = (
            f"Source: {archive_url}\n"
            f"Archive file: {source_name}\n"
            "Auto-posted from Archive.org pipeline."
        )
        print(f"Uploading full video to YouTube: {identifier}")
        full_id = upload_youtube_video(
            youtube,
            full_path,
            title=full_title,
            description=full_desc,
            privacy_status=privacy_status,
        )
        record["full_video_id"] = full_id
        updated = True
        messages.append(f"- `{identifier}` full: https://www.youtube.com/watch?v={full_id}")

    if not short_done:
        print(f"Creating short video: {identifier}")
        make_vertical_short(source_path, short_path)
        short_title = shorten_title(f"{base_title} | Short #Shorts")
        short_desc = (
            f"Source: {archive_url}\n"
            "Auto-generated short from original video.\n"
            "#Shorts"
        )
        print(f"Uploading short video to YouTube: {identifier}")
        short_id = upload_youtube_video(
            youtube,
            short_path,
            title=short_title,
            description=short_desc,
            privacy_status=privacy_status,
        )
        record["short_video_id"] = short_id
        updated = True
        messages.append(f"- `{identifier}` short: https://www.youtube.com/watch?v={short_id}")

    record["archive_url"] = archive_url
    record["archive_file"] = source_name
    record["archive_file_size"] = source_size
    record["updated_at"] = now_iso()
    state[identifier] = record
    return updated, messages


def main() -> None:
    os.chdir(ROOT_DIR)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.touch(exist_ok=True)
    if STATE_FILE.read_text(encoding="utf-8").strip() == "":
        save_state({})

    archive_prefix = os.getenv("ARCHIVE_PREFIX", "gp_").strip() or "gp_"
    max_items = env_int("MAX_ITEMS_PER_RUN", 1)
    max_scan = env_int("MAX_SCAN_ITEMS", 300)
    privacy_status = os.getenv("YT_PRIVACY_STATUS", "public").strip().lower() or "public"
    if privacy_status not in {"public", "unlisted", "private"}:
        privacy_status = "public"

    state = load_state()
    identifiers = archive_search(prefix=archive_prefix, max_scan=max_scan)
    if not identifiers:
        print("No archive identifiers found.")
        write_summary(["## Social Publish", "- No archive items found to process."])
        return

    youtube = get_youtube_client()
    processed = 0
    uploaded_full = 0
    uploaded_short = 0
    summary_lines: List[str] = ["## Social Publish Results"]

    for identifier in identifiers:
        if processed >= max_items:
            break
        metadata = fetch_archive_metadata(identifier)
        before = state.get(identifier, {})
        before_full = bool(before.get("full_video_id"))
        before_short = bool(before.get("short_video_id"))

        try:
            changed, messages = process_identifier(
                identifier=identifier,
                metadata=metadata,
                state=state,
                youtube=youtube,
                privacy_status=privacy_status,
            )
        except HttpError as err:
            die(f"YouTube API error for {identifier}: {err}", code=1)

        if changed:
            save_state(state)
        for line in messages:
            print(line)
            summary_lines.append(line)

        after = state.get(identifier, {})
        if (not before_full) and bool(after.get("full_video_id")):
            uploaded_full += 1
        if (not before_short) and bool(after.get("short_video_id")):
            uploaded_short += 1
        if (not before_full or not before_short) and (bool(after.get("full_video_id")) and bool(after.get("short_video_id"))):
            processed += 1

    summary_lines.extend(
        [
            f"- Archive prefix: `{archive_prefix}`",
            f"- Items completed this run: `{processed}`",
            f"- Full videos uploaded: `{uploaded_full}`",
            f"- Shorts uploaded: `{uploaded_short}`",
        ]
    )
    write_summary(summary_lines)
    print(
        "Summary: "
        f"items_completed={processed}, full_uploaded={uploaded_full}, short_uploaded={uploaded_short}"
    )

    if processed == 0 and (uploaded_full == 0 and uploaded_short == 0):
        print("No new publish actions in this run.")


if __name__ == "__main__":
    main()
