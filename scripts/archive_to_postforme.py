#!/usr/bin/env python3
"""
Archive.org -> processed videos -> PostForMe scheduled social posts.

This script:
1) Finds new archive.org items by identifier prefix.
2) Downloads each source video.
3) Builds a horizontal full video and a vertical short.
4) Uploads processed videos to PostForMe media storage.
5) Creates scheduled social posts via PostForMe API.
6) Saves progress in postforme_state.json to avoid duplicate posting.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

import requests

ARCHIVE_ADVANCEDSEARCH = "https://archive.org/advancedsearch.php"
ARCHIVE_METADATA = "https://archive.org/metadata"
ARCHIVE_DOWNLOAD = "https://archive.org/download"

ROOT_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = ROOT_DIR / "tmp" / "archive-postforme"
STATE_FILE = ROOT_DIR / "postforme_state.json"


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


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "y", "on"}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_summary(lines: List[str]) -> None:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY", "").strip()
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def load_state() -> Dict[str, dict]:
    if not STATE_FILE.exists():
        return {}
    text = STATE_FILE.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def save_state(state: Dict[str, dict]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def archive_search(prefix: str, max_scan: int) -> List[str]:
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
        docs = response.json().get("response", {}).get("docs", [])
        if not docs:
            break
        for doc in docs:
            identifier = str(doc.get("identifier", "")).strip()
            if identifier:
                identifiers.append(identifier)
                if len(identifiers) >= max_scan:
                    break
        page += 1

    output: List[str] = []
    seen = set()
    for identifier in identifiers:
        if identifier in seen:
            continue
        seen.add(identifier)
        output.append(identifier)
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
        lower = name.lower()
        if not lower.endswith(".mp4"):
            continue
        if "thumb" in lower or "preview" in lower:
            continue
        size_raw = str(file_obj.get("size", "0")).strip()
        try:
            size = int(size_raw)
        except ValueError:
            size = 0
        if size > 0:
            candidates.append((name, size))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0]


def download_archive_file(identifier: str, filename: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    url = f"{ARCHIVE_DOWNLOAD}/{identifier}/{quote(filename, safe='/')}"
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


def make_full_horizontal(source: Path, output_path: Path) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-vf",
        "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
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
        str(output_path),
    ]
    run_command(command, "Failed creating full horizontal video.")


def make_vertical_short(source: Path, output_path: Path) -> None:
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
        str(output_path),
    ]
    run_command(command, "Failed creating short vertical video.")


class PostForMeClient:
    def __init__(self, api_key: str, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, *, params=None, json_body=None) -> dict:
        url = f"{self.base_url}{path}"
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            params=params,
            json=json_body,
            timeout=60,
        )
        if response.status_code >= 400:
            die(f"PostForMe API error ({response.status_code}) {path}: {response.text}")
        if not response.text:
            return {}
        return response.json()

    def get_connected_social_accounts(self, platforms: List[str]) -> List[str]:
        account_ids: List[str] = []
        params = {"status": "connected", "limit": 100, "offset": 0}
        for platform in platforms:
            params.setdefault("platform", [])
            params["platform"].append(platform)

        while True:
            payload = self._request("GET", "/social-accounts", params=params)
            data = payload.get("data", [])
            for item in data:
                account_id = str(item.get("id", "")).strip()
                if account_id:
                    account_ids.append(account_id)
            next_url = payload.get("meta", {}).get("next")
            if not next_url:
                break
            params["offset"] = int(params.get("offset", 0)) + int(params.get("limit", 100))

        unique: List[str] = []
        seen = set()
        for account_id in account_ids:
            if account_id in seen:
                continue
            seen.add(account_id)
            unique.append(account_id)
        return unique

    def create_upload_url(self) -> Tuple[str, str]:
        payload = self._request("POST", "/media/create-upload-url")
        upload_url = str(payload.get("upload_url", "")).strip()
        media_url = str(payload.get("media_url", "")).strip()
        if not upload_url or not media_url:
            die(f"Invalid /media/create-upload-url response: {payload}")
        return upload_url, media_url

    def upload_file_to_signed_url(self, upload_url: str, file_path: Path) -> None:
        with open(file_path, "rb") as fh:
            response = requests.put(
                upload_url,
                data=fh,
                headers={"Content-Type": "video/mp4"},
                timeout=300,
            )
        if response.status_code >= 400:
            die(f"Failed uploading media file ({response.status_code}): {response.text}")

    def create_social_post(
        self,
        *,
        caption: str,
        media_url: str,
        social_accounts: List[str],
        scheduled_at: str,
        external_id: str,
        skip_processing: bool,
    ) -> dict:
        payload = {
            "caption": caption,
            "scheduled_at": scheduled_at,
            "media": [{"url": media_url, "skip_processing": skip_processing}],
            "social_accounts": social_accounts,
            "external_id": external_id,
            "isDraft": False,
        }
        return self._request("POST", "/social-posts", json_body=payload)


def build_caption(template: str, *, title: str, archive_url: str, identifier: str, variant: str) -> str:
    return template.format(
        title=title,
        archive_url=archive_url,
        identifier=identifier,
        variant=variant,
    )


def schedule_times_for_index(
    idx: int,
    *,
    full_offset_minutes: int,
    short_offset_minutes: int,
    item_spacing_minutes: int,
) -> Tuple[str, str]:
    now = datetime.now(timezone.utc)
    full_at = now + timedelta(minutes=full_offset_minutes + (idx * item_spacing_minutes))
    short_at = now + timedelta(minutes=short_offset_minutes + (idx * item_spacing_minutes))
    return (
        full_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        short_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )


def process_identifier(
    *,
    identifier: str,
    metadata: dict,
    state: Dict[str, dict],
    client: PostForMeClient,
    account_ids: List[str],
    full_scheduled_at: str,
    short_scheduled_at: str,
    full_caption_template: str,
    short_caption_template: str,
    skip_processing: bool,
    dry_run: bool,
) -> Tuple[bool, List[str]]:
    messages: List[str] = []
    updated = False

    record = state.get(identifier, {})
    full_done = bool(record.get("full_post_id"))
    short_done = bool(record.get("short_post_id"))
    if full_done and short_done:
        messages.append(f"- `{identifier}` already completed, skipped.")
        return updated, messages

    source_choice = choose_source_file(metadata)
    if not source_choice:
        messages.append(f"- `{identifier}` skipped: no usable mp4 source.")
        return updated, messages

    source_name, source_size = source_choice
    archive_url = f"https://archive.org/details/{identifier}"
    title = str(metadata.get("metadata", {}).get("title", identifier)).strip() or identifier
    work_dir = TMP_DIR / identifier
    work_dir.mkdir(parents=True, exist_ok=True)
    source_path = work_dir / "source.mp4"
    full_path = work_dir / "full.mp4"
    short_path = work_dir / "short.mp4"

    print(f"Processing archive item: {identifier}")
    download_archive_file(identifier, source_name, source_path)
    make_full_horizontal(source_path, full_path)
    make_vertical_short(source_path, short_path)

    full_external_id = f"{identifier}:full"
    short_external_id = f"{identifier}:short"

    if not full_done:
        full_caption = build_caption(
            full_caption_template,
            title=title,
            archive_url=archive_url,
            identifier=identifier,
            variant="full",
        )
        if dry_run:
            full_post_id = "dryrun-full"
            full_media_url = "dryrun://media/full"
        else:
            full_upload_url, full_media_url = client.create_upload_url()
            client.upload_file_to_signed_url(full_upload_url, full_path)
            full_post = client.create_social_post(
                caption=full_caption,
                media_url=full_media_url,
                social_accounts=account_ids,
                scheduled_at=full_scheduled_at,
                external_id=full_external_id,
                skip_processing=skip_processing,
            )
            full_post_id = str(full_post.get("id", "")).strip()
            if not full_post_id:
                die(f"Invalid post response for full variant on {identifier}: {full_post}")
        record["full_post_id"] = full_post_id
        record["full_media_url"] = full_media_url
        record["full_scheduled_at"] = full_scheduled_at
        updated = True
        messages.append(f"- `{identifier}` full scheduled `{full_scheduled_at}` (post_id: `{full_post_id}`)")

    if not short_done:
        short_caption = build_caption(
            short_caption_template,
            title=title,
            archive_url=archive_url,
            identifier=identifier,
            variant="short",
        )
        if dry_run:
            short_post_id = "dryrun-short"
            short_media_url = "dryrun://media/short"
        else:
            short_upload_url, short_media_url = client.create_upload_url()
            client.upload_file_to_signed_url(short_upload_url, short_path)
            short_post = client.create_social_post(
                caption=short_caption,
                media_url=short_media_url,
                social_accounts=account_ids,
                scheduled_at=short_scheduled_at,
                external_id=short_external_id,
                skip_processing=skip_processing,
            )
            short_post_id = str(short_post.get("id", "")).strip()
            if not short_post_id:
                die(f"Invalid post response for short variant on {identifier}: {short_post}")
        record["short_post_id"] = short_post_id
        record["short_media_url"] = short_media_url
        record["short_scheduled_at"] = short_scheduled_at
        updated = True
        messages.append(f"- `{identifier}` short scheduled `{short_scheduled_at}` (post_id: `{short_post_id}`)")

    record["archive_url"] = archive_url
    record["archive_source_name"] = source_name
    record["archive_source_size"] = source_size
    record["updated_at"] = now_iso()
    state[identifier] = record
    return updated, messages


def main() -> None:
    os.chdir(ROOT_DIR)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        STATE_FILE.write_text("{}\n", encoding="utf-8")

    api_key = env_required("POSTFORME_API_KEY")
    base_url = os.getenv("POSTFORME_BASE_URL", "https://api.postforme.dev/v1").strip() or "https://api.postforme.dev/v1"
    archive_prefix = os.getenv("ARCHIVE_PREFIX", "gp_").strip() or "gp_"
    max_items = env_int("MAX_ITEMS_PER_RUN", 1)
    max_scan_items = env_int("MAX_SCAN_ITEMS", 300)
    full_offset_minutes = env_int("FULL_OFFSET_MINUTES", 20)
    short_offset_minutes = env_int("SHORT_OFFSET_MINUTES", 80)
    item_spacing_minutes = env_int("ITEM_SPACING_MINUTES", 240)
    skip_processing = env_bool("POSTFORME_SKIP_MEDIA_PROCESSING", False)
    dry_run = env_bool("DRY_RUN", False)

    full_caption_template = os.getenv(
        "FULL_CAPTION_TEMPLATE",
        "{title}\n\nSource: {archive_url}",
    )
    short_caption_template = os.getenv(
        "SHORT_CAPTION_TEMPLATE",
        "{title}\n\nShort clip\nSource: {archive_url}\n#shorts",
    )

    platforms_raw = os.getenv("POSTFORME_PLATFORMS", "").strip()
    platforms = [p.strip().lower() for p in platforms_raw.split(",") if p.strip()]

    state = load_state()
    client = PostForMeClient(api_key=api_key, base_url=base_url)
    account_ids = client.get_connected_social_accounts(platforms=platforms)
    if not account_ids:
        die("No connected social accounts found in PostForMe for selected platform filters.")

    identifiers = archive_search(prefix=archive_prefix, max_scan=max_scan_items)
    if not identifiers:
        print("No archive items found.")
        write_summary(
            [
                "## Archive to PostForMe",
                "- No archive items found.",
            ]
        )
        return

    completed_items = 0
    scheduled_full = 0
    scheduled_short = 0
    summary_lines = [
        "## Archive to PostForMe",
        f"- Archive prefix: `{archive_prefix}`",
        f"- Connected accounts targeted: `{len(account_ids)}`",
    ]

    for identifier in identifiers:
        if completed_items >= max_items:
            break
        current_record = state.get(identifier, {})
        if current_record.get("full_post_id") and current_record.get("short_post_id"):
            continue

        full_at, short_at = schedule_times_for_index(
            completed_items,
            full_offset_minutes=full_offset_minutes,
            short_offset_minutes=short_offset_minutes,
            item_spacing_minutes=item_spacing_minutes,
        )
        metadata = fetch_archive_metadata(identifier)
        changed, messages = process_identifier(
            identifier=identifier,
            metadata=metadata,
            state=state,
            client=client,
            account_ids=account_ids,
            full_scheduled_at=full_at,
            short_scheduled_at=short_at,
            full_caption_template=full_caption_template,
            short_caption_template=short_caption_template,
            skip_processing=skip_processing,
            dry_run=dry_run,
        )
        for line in messages:
            print(line)
            summary_lines.append(line)
        if changed:
            save_state(state)
            record = state.get(identifier, {})
            if record.get("full_post_id"):
                scheduled_full += 1
            if record.get("short_post_id"):
                scheduled_short += 1
            if record.get("full_post_id") and record.get("short_post_id"):
                completed_items += 1

    summary_lines.extend(
        [
            f"- Completed items this run: `{completed_items}`",
            f"- Full posts scheduled: `{scheduled_full}`",
            f"- Short posts scheduled: `{scheduled_short}`",
            f"- Dry run: `{str(dry_run).lower()}`",
        ]
    )
    write_summary(summary_lines)
    print(
        "Summary: "
        f"completed_items={completed_items}, full_scheduled={scheduled_full}, short_scheduled={scheduled_short}"
    )


if __name__ == "__main__":
    main()
