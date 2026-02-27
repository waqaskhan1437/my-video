#!/usr/bin/env python3
import hashlib
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests

SCOPE = "https://www.googleapis.com/auth/photospicker.mediaitems.readonly"
API_BASE = "https://photospicker.googleapis.com/v1"
TOKEN_URL = "https://oauth2.googleapis.com/token"

ROOT_DIR = Path(__file__).resolve().parent.parent
TMP_INPUT = ROOT_DIR / "tmp" / "input"
TMP_OUTPUT = ROOT_DIR / "tmp" / "output"
PROCESSED_FILE = ROOT_DIR / "processed.txt"


def die(message: str, code: int = 1) -> None:
    print(message)
    sys.exit(code)


def env_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        die(f"Missing required env var: {name}")
    return value


def write_summary(lines) -> None:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY", "").strip()
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def refresh_access_token() -> str:
    payload = {
        "client_id": env_required("GOOGLE_CLIENT_ID"),
        "client_secret": env_required("GOOGLE_CLIENT_SECRET"),
        "refresh_token": env_required("GOOGLE_REFRESH_TOKEN"),
        "grant_type": "refresh_token",
    }
    response = requests.post(TOKEN_URL, data=payload, timeout=45)
    if response.status_code >= 400:
        die(f"Google token refresh failed ({response.status_code}): {response.text}")
    access_token = response.json().get("access_token", "").strip()
    if not access_token:
        die("Google token refresh succeeded but access_token is missing.")
    return access_token


def api_request(method: str, path: str, access_token: str, *, params=None, json_body=None):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.request(
        method=method,
        url=f"{API_BASE}{path}",
        headers=headers,
        params=params,
        json=json_body,
        timeout=60,
    )
    if response.status_code >= 400:
        die(f"Google Photos API error ({response.status_code}) on {path}: {response.text}")
    if not response.text:
        return {}
    return response.json()


def parse_duration_seconds(value: str, default_seconds: float) -> float:
    if not value:
        return default_seconds
    raw = value.strip().lower()
    if raw.endswith("s"):
        raw = raw[:-1]
    try:
        parsed = float(raw)
        return parsed if parsed > 0 else default_seconds
    except ValueError:
        return default_seconds


def normalize_session_id(raw_value: str) -> str:
    value = raw_value.strip()
    if value.startswith("sessions/"):
        return value.split("/", 1)[1]
    return value


def create_session(access_token: str, max_item_count: int):
    payload = {}
    if max_item_count > 0:
        payload = {"pickingConfig": {"maxItemCount": max_item_count}}
    data = api_request("POST", "/sessions", access_token, json_body=payload)
    session_id = data.get("id", "")
    picker_uri = data.get("pickerUri", "")
    if not session_id or not picker_uri:
        die(f"Unexpected create session response: {data}")
    print(f"SESSION_ID={session_id}")
    print(f"PICKER_URI={picker_uri}")
    write_summary(
        [
            "## Google Photos Picker Session",
            f"- Session ID: `{session_id}`",
            f"- Picker URL: {picker_uri}",
            "- Open picker URL, select videos, click Done, then rerun workflow in `process_session` mode.",
        ]
    )


def get_session(access_token: str, session_id: str):
    return api_request("GET", f"/sessions/{session_id}", access_token)


def wait_for_selection(access_token: str, session_id: str):
    session = get_session(access_token, session_id)
    polling = session.get("pollingConfig", {})
    poll_interval = parse_duration_seconds(polling.get("pollInterval", ""), 4.0)
    timeout_seconds = parse_duration_seconds(polling.get("timeoutIn", ""), 600.0)

    started_at = time.monotonic()
    while not session.get("mediaItemsSet", False):
        elapsed = time.monotonic() - started_at
        if elapsed >= timeout_seconds:
            die("Selection timeout: user did not finish picking media items in time.")
        sleep_for = min(poll_interval, timeout_seconds - elapsed)
        print(f"Waiting for user selection... retry in {sleep_for:.1f}s")
        time.sleep(sleep_for)
        session = get_session(access_token, session_id)

    print("Selection confirmed (mediaItemsSet=true).")
    return session


def list_media_items(access_token: str, session_id: str):
    items = []
    page_token = ""
    while True:
        params = {"sessionId": session_id, "pageSize": 100}
        if page_token:
            params["pageToken"] = page_token
        data = api_request("GET", "/mediaItems", access_token, params=params)
        items.extend(data.get("mediaItems", []))
        page_token = data.get("nextPageToken", "")
        if not page_token:
            break
    return items


def try_delete_session(access_token: str, session_id: str) -> None:
    response = requests.delete(
        f"{API_BASE}/sessions/{session_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=45,
    )
    if response.status_code in (200, 204, 404):
        print(f"Session cleanup completed: {session_id}")
        return
    print(f"Warning: failed to delete session {session_id} ({response.status_code})")


def load_processed_ids():
    if not PROCESSED_FILE.exists():
        return set()
    content = PROCESSED_FILE.read_text(encoding="utf-8")
    return {line.strip() for line in content.splitlines() if line.strip()}


def append_processed_id(item_id: str) -> None:
    with open(PROCESSED_FILE, "a", encoding="utf-8") as fh:
        fh.write(item_id + "\n")


def sanitize_prefix(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9_.-]", "-", value.lower()).strip("-")
    return cleaned or "gp"


def run_command(command):
    result = subprocess.run(command, text=True)
    return result.returncode == 0


def download_video(access_token: str, item: dict, destination: Path) -> bool:
    media_file = item.get("mediaFile", {})
    base_url = media_file.get("baseUrl", "")
    if not base_url:
        print(f"Skipping item without baseUrl: {item.get('id', 'unknown')}")
        return False

    video_meta = media_file.get("mediaFileMetadata", {}).get("videoMetadata", {})
    processing_status = video_meta.get("processingStatus", "")
    if processing_status and processing_status != "READY":
        print(f"Skipping item (processingStatus={processing_status}).")
        return False

    download_url = f"{base_url}=dv"
    response = requests.get(
        download_url,
        headers={"Authorization": f"Bearer {access_token}"},
        stream=True,
        timeout=120,
    )
    if response.status_code >= 400:
        print(f"Download failed ({response.status_code}) for item {item.get('id', 'unknown')}")
        return False

    with open(destination, "wb") as fh:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                fh.write(chunk)
    return True


def compress_video(source_path: Path, output_path: Path) -> bool:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-vf",
        "scale=1280:-2:force_original_aspect_ratio=decrease",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "28",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    return run_command(command)


def upload_to_archive(identifier: str, file_path: Path) -> bool:
    command = [
        "ia",
        "upload",
        identifier,
        str(file_path),
        f"--metadata=title:{identifier}",
        "--metadata=mediatype:movies",
        "--metadata=source:google-photos-picker",
        "--retries=5",
    ]
    return run_command(command)


def process_session(access_token: str, session_id: str, archive_prefix: str) -> None:
    wait_for_selection(access_token, session_id)
    items = list_media_items(access_token, session_id)
    if not items:
        die("No media items found in this picker session.")

    processed = load_processed_ids()
    TMP_INPUT.mkdir(parents=True, exist_ok=True)
    TMP_OUTPUT.mkdir(parents=True, exist_ok=True)

    attempted = 0
    uploaded = 0
    failed = 0

    for item in items:
        item_id = item.get("id", "").strip()
        media_file = item.get("mediaFile", {})
        mime_type = media_file.get("mimeType", "").lower()
        if not item_id:
            continue
        if not mime_type.startswith("video/"):
            continue
        if item_id in processed:
            print(f"Skipping already processed item: {item_id}")
            continue

        attempted += 1
        item_hash = hashlib.sha1(item_id.encode("utf-8")).hexdigest()[:16]
        identifier = f"{archive_prefix}_{item_hash}"

        source_file = TMP_INPUT / f"{item_hash}.source"
        output_file = TMP_OUTPUT / f"{item_hash}.mp4"
        if source_file.exists():
            source_file.unlink()
        if output_file.exists():
            output_file.unlink()

        print(f"Downloading item: {item_id}")
        if not download_video(access_token, item, source_file):
            failed += 1
            continue

        print(f"Compressing item: {item_id}")
        if not compress_video(source_file, output_file):
            print(f"Compression failed for item: {item_id}")
            failed += 1
            continue

        print(f"Uploading to archive.org: {identifier}")
        if not upload_to_archive(identifier, output_file):
            print(f"Upload failed for item: {item_id}")
            failed += 1
            continue

        append_processed_id(item_id)
        processed.add(item_id)
        uploaded += 1
        print(f"Uploaded: https://archive.org/details/{identifier}")

    print(f"Summary: attempted={attempted}, uploaded={uploaded}, failed={failed}")
    write_summary(
        [
            "## Process Summary",
            f"- Session ID: `{session_id}`",
            f"- Attempted videos: `{attempted}`",
            f"- Uploaded videos: `{uploaded}`",
            f"- Failed videos: `{failed}`",
        ]
    )

    try_delete_session(access_token, session_id)

    if attempted > 0 and uploaded == 0:
        die("No uploads completed.", code=1)


def main() -> None:
    os.chdir(ROOT_DIR)
    PROCESSED_FILE.touch(exist_ok=True)

    mode = os.getenv("RUN_MODE", "create_session").strip()
    session_id = normalize_session_id(os.getenv("PICKER_SESSION_ID", ""))
    max_item_raw = os.getenv("PICKER_MAX_ITEM_COUNT", "0").strip()
    archive_prefix = sanitize_prefix(os.getenv("ARCHIVE_PREFIX", "gp"))

    try:
        max_item_count = int(max_item_raw)
    except ValueError:
        max_item_count = 0

    access_token = refresh_access_token()

    if mode == "create_session":
        create_session(access_token, max_item_count=max_item_count)
        return

    if mode == "process_session":
        if not session_id:
            die("process_session mode requires PICKER_SESSION_ID input.")
        if not os.getenv("IA_ACCESS_KEY", "").strip() or not os.getenv("IA_SECRET_KEY", "").strip():
            die("Missing IA_ACCESS_KEY / IA_SECRET_KEY for process_session mode.")
        process_session(access_token, session_id=session_id, archive_prefix=archive_prefix)
        return

    die(f"Unsupported mode: {mode}. Use create_session or process_session.")


if __name__ == "__main__":
    main()
