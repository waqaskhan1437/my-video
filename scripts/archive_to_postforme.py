
#!/usr/bin/env python3
"""
Archive.org + external links -> PostForMe scheduling automation.

Features:
- Multiple automation profiles from JSON config
- Window modes: new_since_last_run, last_x_days, specific_date, all
- Per-automation PostForMe account targeting
- External links source + archive source
- Dedupe state per automation (optional global dedupe)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlparse

import requests

ARCHIVE_ADVANCEDSEARCH = "https://archive.org/advancedsearch.php"
ARCHIVE_METADATA = "https://archive.org/metadata"
ARCHIVE_DOWNLOAD = "https://archive.org/download"

ROOT_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = ROOT_DIR / "tmp" / "archive-postforme"
STATE_FILE = ROOT_DIR / "postforme_state.json"
DEFAULT_AUTOMATION_CONFIG = ROOT_DIR / "automations" / "postforme_automations.json"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv", ".webm"}


def die(message: str, code: int = 1) -> None:
    print(message)
    sys.exit(code)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def now_iso() -> str:
    return to_iso_z(now_utc())


def env_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        die(f"Missing required env var: {name}")
    return value


def env_str(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    return value if value else default


def parse_int(value: Any, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def env_int(name: str, default: int, minimum: Optional[int] = None) -> int:
    raw = os.getenv(name, "").strip()
    value = parse_int(raw, default) if raw else default
    if minimum is not None and value < minimum:
        return default
    return value


def parse_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raw = str(value).strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "y", "on"}


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    return parse_bool(raw, default)


def parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                dt = datetime.strptime(raw, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_date_only(value: Any) -> Optional[date]:
    raw = str(value).strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def slugify(value: str, fallback: str = "item") -> str:
    out = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    return out or fallback


def sha1_short(value: str, length: int = 12) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:length]


def unique_strings(values: List[str]) -> List[str]:
    output: List[str] = []
    seen = set()
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def normalize_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return unique_strings([str(item).strip() for item in value if str(item).strip()])
    if isinstance(value, str):
        return unique_strings([part.strip() for part in value.split(",") if part.strip()])
    return []


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
    run_command(command, "ffmpeg full conversion failed")


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
    run_command(command, "ffmpeg short conversion failed")


def write_summary(lines: List[str]) -> None:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY", "").strip()
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def resolve_repo_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return (ROOT_DIR / path).resolve()


def load_state() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {"version": 2, "automations": {}}
    raw = STATE_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        return {"version": 2, "automations": {}}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"version": 2, "automations": {}}

    if not isinstance(parsed, dict):
        return {"version": 2, "automations": {}}

    if "automations" in parsed and isinstance(parsed.get("automations"), dict):
        parsed.setdefault("version", 2)
        return parsed

    # Legacy migration: flat identifier keys -> legacy automation bucket
    legacy_items: Dict[str, Any] = {}
    for key, value in parsed.items():
        if not isinstance(value, dict):
            continue
        if not (value.get("full_post_id") or value.get("short_post_id")):
            continue
        legacy_items[f"archive:{key}"] = value

    return {
        "version": 2,
        "automations": {
            "legacy": {
                "last_run_at": "",
                "items": legacy_items,
            }
        },
    }


def save_state(state: Dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    if not path.exists():
        die(f"Missing file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"Invalid JSON in {path}: {exc}")


def archive_search(prefix: str, max_scan: int) -> List[Dict[str, str]]:
    output: List[Dict[str, str]] = []
    page = 1
    rows = 100
    query = f"identifier:{prefix}* AND mediatype:movies"

    while len(output) < max_scan:
        params = {
            "q": query,
            "fl[]": ["identifier", "publicdate", "title"],
            "sort[]": "publicdate desc",
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
            if not identifier:
                continue
            output.append(
                {
                    "identifier": identifier,
                    "publicdate": str(doc.get("publicdate", "")).strip(),
                    "title": str(doc.get("title", "")).strip(),
                }
            )
            if len(output) >= max_scan:
                break

        page += 1

    deduped: List[Dict[str, str]] = []
    seen = set()
    for item in output:
        identifier = item["identifier"]
        if identifier in seen:
            continue
        seen.add(identifier)
        deduped.append(item)
    return deduped


def fetch_archive_metadata(identifier: str) -> Dict[str, Any]:
    response = requests.get(f"{ARCHIVE_METADATA}/{identifier}", timeout=60)
    if response.status_code >= 400:
        die(f"Archive metadata failed ({response.status_code}) for {identifier}: {response.text}")
    payload = response.json()
    if not isinstance(payload, dict):
        die(f"Invalid archive metadata payload for {identifier}")
    return payload


def choose_archive_source(metadata: Dict[str, Any]) -> Optional[Tuple[str, int]]:
    candidates: List[Tuple[str, int]] = []
    for file_obj in metadata.get("files", []):
        if not isinstance(file_obj, dict):
            continue
        name = str(file_obj.get("name", "")).strip()
        lower = name.lower()
        if not lower.endswith(".mp4"):
            continue
        if "thumb" in lower or "preview" in lower:
            continue
        size = parse_int(file_obj.get("size", 0), 0)
        if size > 0:
            candidates.append((name, size))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[1], reverse=True)
    return candidates[0]


def download_archive_video(identifier: str, filename: str, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_url = f"{ARCHIVE_DOWNLOAD}/{identifier}/{quote(filename, safe='/')}"
    print(f"Downloading archive source: {source_url}")
    with requests.get(source_url, stream=True, timeout=180) as response:
        if response.status_code >= 400:
            die(f"Archive download failed ({response.status_code}) for {source_url}")
        with open(destination, "wb") as fh:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    fh.write(chunk)
    return source_url


def download_direct(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=180) as response:
        if response.status_code >= 400:
            die(f"External download failed ({response.status_code}) for {url}")
        with open(output_path, "wb") as fh:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    fh.write(chunk)


def download_external_video(url: str, destination_prefix: Path) -> Path:
    destination_prefix.parent.mkdir(parents=True, exist_ok=True)
    extension = Path(urlparse(url).path).suffix.lower()

    if extension in VIDEO_EXTENSIONS:
        output = destination_prefix.with_suffix(extension)
        print(f"Downloading external direct source: {url}")
        download_direct(url, output)
        return output

    print(f"Downloading external source via yt-dlp: {url}")
    template = str(destination_prefix) + ".%(ext)s"
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
        url,
    ]
    run_command(command, f"yt-dlp failed for URL: {url}")

    files = sorted(
        destination_prefix.parent.glob(destination_prefix.name + ".*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not files:
        die(f"yt-dlp output not found for URL: {url}")

    preferred = [path for path in files if path.suffix.lower() in VIDEO_EXTENSIONS]
    return preferred[0] if preferred else files[0]


class PostForMeClient:
    def __init__(self, api_key: str, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        response = requests.request(
            method=method,
            url=f"{self.base_url}{path}",
            headers=self.headers,
            params=params,
            json=json_body,
            timeout=timeout,
        )
        if response.status_code >= 400:
            die(f"PostForMe API error ({response.status_code}) {path}: {response.text}")
        if not response.text:
            return {}
        payload = response.json()
        if isinstance(payload, dict):
            return payload
        return {}

    def list_social_accounts(self, platforms: List[str]) -> List[Dict[str, Any]]:
        accounts: List[Dict[str, Any]] = []
        limit = 100
        offset = 0

        while True:
            params: Dict[str, Any] = {
                "status": "connected",
                "limit": limit,
                "offset": offset,
            }
            if platforms:
                params["platform"] = platforms

            payload = self._request("GET", "/social-accounts", params=params)
            data = payload.get("data", [])
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        accounts.append(item)

            meta = payload.get("meta", {})
            if not (isinstance(meta, dict) and meta.get("next")):
                break
            offset += limit

        return accounts

    def create_upload_url(self) -> Tuple[str, str]:
        payload = self._request("POST", "/media/create-upload-url")
        upload_url = str(payload.get("upload_url", "")).strip()
        media_url = str(payload.get("media_url", "")).strip()
        if not upload_url or not media_url:
            die(f"Invalid /media/create-upload-url response: {payload}")
        return upload_url, media_url

    def upload_file(self, upload_url: str, file_path: Path) -> None:
        with open(file_path, "rb") as fh:
            response = requests.put(
                upload_url,
                data=fh,
                headers={"Content-Type": "video/mp4"},
                timeout=600,
            )
        if response.status_code >= 400:
            die(f"PostForMe media upload failed ({response.status_code}): {response.text}")

    def create_post(
        self,
        *,
        caption: str,
        scheduled_at: str,
        media_url: str,
        social_accounts: List[str],
        external_id: str,
        skip_processing: bool,
    ) -> Dict[str, Any]:
        payload = {
            "caption": caption,
            "scheduled_at": scheduled_at,
            "media": [{"url": media_url, "skip_processing": skip_processing}],
            "social_accounts": social_accounts,
            "external_id": external_id,
            "isDraft": False,
        }
        return self._request("POST", "/social-posts", json_body=payload)


def is_record_complete(record: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(record, dict):
        return False
    return bool(record.get("full_post_id")) and bool(record.get("short_post_id"))


def completed_in_other_automation(state: Dict[str, Any], automation_id: str, source_key: str) -> Optional[str]:
    automations = state.get("automations", {})
    if not isinstance(automations, dict):
        return None

    for other_id, other_state in automations.items():
        if other_id == automation_id or not isinstance(other_state, dict):
            continue
        items = other_state.get("items", {})
        if not isinstance(items, dict):
            continue
        if is_record_complete(items.get(source_key)):
            return other_id
    return None


def in_window(
    item_datetime: Optional[datetime],
    *,
    mode: str,
    last_run_at: Optional[datetime],
    last_x_days: int,
    specific_date: Optional[date],
) -> bool:
    mode = mode.strip().lower()
    if mode == "all":
        return True

    if mode == "new_since_last_run":
        if last_run_at is None:
            return True
        if item_datetime is None:
            return True
        return item_datetime > last_run_at

    if mode == "last_x_days":
        if item_datetime is None:
            return False
        return item_datetime >= (now_utc() - timedelta(days=max(1, last_x_days)))

    if mode == "specific_date":
        if specific_date is None:
            return True
        if item_datetime is None:
            return False
        return item_datetime.date() == specific_date

    return True


def load_external_links(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        print(f"External links file missing, skipping: {path}")
        return []

    payload = load_json(path)
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        links = payload.get("links", [])
        items = links if isinstance(links, list) else []
    else:
        items = []

    output: List[Dict[str, str]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        if not parse_bool(item.get("enabled", True), True):
            continue
        url = str(item.get("url", "")).strip()
        if not url:
            continue
        item_id = str(item.get("id", "")).strip() or f"ext-{index}-{sha1_short(url)}"
        title = str(item.get("title", "")).strip() or item_id
        item_date = (
            str(item.get("date", "")).strip()
            or str(item.get("published_at", "")).strip()
            or str(item.get("created_at", "")).strip()
        )
        output.append(
            {
                "id": item_id,
                "url": url,
                "title": title,
                "date": item_date,
            }
        )
    return output


def build_archive_candidates(
    *,
    archive_prefix: str,
    max_scan_items: int,
    mode: str,
    last_run_at: Optional[datetime],
    last_x_days: int,
    specific_date: Optional[date],
) -> List[Dict[str, Any]]:
    docs = archive_search(archive_prefix, max_scan_items)
    candidates: List[Dict[str, Any]] = []

    for doc in docs:
        identifier = doc["identifier"]
        source_dt = parse_datetime(doc.get("publicdate", ""))
        if not in_window(
            source_dt,
            mode=mode,
            last_run_at=last_run_at,
            last_x_days=last_x_days,
            specific_date=specific_date,
        ):
            continue
        candidates.append(
            {
                "source_type": "archive",
                "source_key": f"archive:{identifier}",
                "source_id": identifier,
                "source_datetime": source_dt,
                "title": doc.get("title", "") or identifier,
                "source_url": f"https://archive.org/details/{identifier}",
            }
        )
    return candidates


def build_external_candidates(
    *,
    links_file: Path,
    link_ids: List[str],
    mode: str,
    last_run_at: Optional[datetime],
    last_x_days: int,
    specific_date: Optional[date],
) -> List[Dict[str, Any]]:
    include_set = set(link_ids)
    items = load_external_links(links_file)
    output: List[Dict[str, Any]] = []

    for item in items:
        item_id = item["id"]
        if include_set and item_id not in include_set:
            continue

        source_dt = parse_datetime(item.get("date", ""))
        if mode in {"last_x_days", "specific_date"} and source_dt is None:
            print(f"Skipping external item {item_id}: date required for selected window mode")
            continue

        if not in_window(
            source_dt,
            mode=mode,
            last_run_at=last_run_at,
            last_x_days=last_x_days,
            specific_date=specific_date,
        ):
            continue

        output.append(
            {
                "source_type": "external",
                "source_key": f"external:{item_id}",
                "source_id": item_id,
                "source_datetime": source_dt,
                "title": item["title"],
                "source_url": item["url"],
                "external_url": item["url"],
            }
        )

    return output


def resolve_account_ids(client: PostForMeClient, account_ids: List[str], platforms: List[str]) -> List[str]:
    explicit = unique_strings(account_ids)
    if explicit:
        return explicit

    resolved: List[str] = []
    for account in client.list_social_accounts(platforms):
        account_id = str(account.get("id", "")).strip()
        if account_id:
            resolved.append(account_id)
    return unique_strings(resolved)


def list_accounts(client: PostForMeClient) -> None:
    accounts = client.list_social_accounts([])
    if not accounts:
        print("No connected PostForMe accounts found")
        write_summary(["## PostForMe Accounts", "- No connected accounts found."])
        return

    lines = ["Connected PostForMe accounts:"]
    summary = ["## PostForMe Accounts"]
    for account in accounts:
        account_id = str(account.get("id", "")).strip()
        platform = str(account.get("platform", "")).strip()
        username = str(account.get("username", "")).strip() or str(account.get("handle", "")).strip() or "-"
        status = str(account.get("status", "")).strip()
        line = f"- id={account_id} platform={platform} account={username} status={status}"
        lines.append(line)
        summary.append(f"- `{account_id}` | `{platform}` | `{username}` | `{status}`")

    print("\n".join(lines))
    write_summary(summary)


def schedule_pair(index: int, full_offset: int, short_offset: int, spacing: int) -> Tuple[str, str]:
    base = now_utc()
    full_time = base + timedelta(minutes=full_offset + (index * spacing))
    short_time = base + timedelta(minutes=short_offset + (index * spacing))
    return to_iso_z(full_time), to_iso_z(short_time)


def format_caption(template: str, values: Dict[str, str], fallback: str) -> str:
    try:
        text = template.format(**values).strip()
    except Exception:
        text = ""
    return text if text else fallback


def make_external_id(automation_id: str, source_key: str, variant: str) -> str:
    return f"{slugify(automation_id, 'auto')}-{variant}-{sha1_short(f'{automation_id}|{source_key}|{variant}', 18)}"


def process_candidate(
    *,
    candidate: Dict[str, Any],
    automation_id: str,
    automation_items: Dict[str, Any],
    client: PostForMeClient,
    account_ids: List[str],
    full_caption_template: str,
    short_caption_template: str,
    full_schedule: str,
    short_schedule: str,
    skip_processing: bool,
    dry_run: bool,
) -> Tuple[bool, str]:
    source_key = candidate["source_key"]
    source_id = candidate["source_id"]
    source_type = candidate["source_type"]
    title = candidate.get("title", source_id)
    source_url = candidate.get("source_url", "")

    item_dir = TMP_DIR / slugify(automation_id) / slugify(source_key, sha1_short(source_key))
    item_dir.mkdir(parents=True, exist_ok=True)

    source_path = item_dir / "source.input"
    full_path = item_dir / "full.mp4"
    short_path = item_dir / "short.mp4"

    source_meta: Dict[str, Any] = {}
    if source_type == "archive":
        metadata = fetch_archive_metadata(source_id)
        selected = choose_archive_source(metadata)
        if not selected:
            return False, f"- `{automation_id}` `{source_id}` skipped: no mp4 source found"
        archive_name, archive_size = selected
        source_url = download_archive_video(source_id, archive_name, source_path)
        title = str(metadata.get("metadata", {}).get("title", "")).strip() or title
        source_meta = {
            "archive_source_name": archive_name,
            "archive_source_size": archive_size,
        }
    else:
        external_url = str(candidate.get("external_url", "")).strip()
        if not external_url:
            return False, f"- `{automation_id}` `{source_id}` skipped: external URL missing"
        source_path = download_external_video(external_url, source_path.with_suffix(""))
        source_url = external_url

    print(f"Compressing full video for {automation_id} / {source_key}")
    make_full_horizontal(source_path, full_path)
    print(f"Compressing short video for {automation_id} / {source_key}")
    make_vertical_short(source_path, short_path)

    full_caption = format_caption(
        full_caption_template,
        {
            "title": title,
            "source_url": source_url,
            "source_id": source_id,
            "variant": "full",
            "automation_id": automation_id,
        },
        f"{title}\n\nSource: {source_url}",
    )
    short_caption = format_caption(
        short_caption_template,
        {
            "title": title,
            "source_url": source_url,
            "source_id": source_id,
            "variant": "short",
            "automation_id": automation_id,
        },
        f"{title}\n\nShort clip\nSource: {source_url}\n#shorts",
    )

    if dry_run:
        seed = sha1_short(f"{automation_id}|{source_key}", 16)
        full_post_id = f"dryrun-full-{seed}"
        short_post_id = f"dryrun-short-{seed}"
        full_media_url = "dryrun://full"
        short_media_url = "dryrun://short"
    else:
        full_upload_url, full_media_url = client.create_upload_url()
        client.upload_file(full_upload_url, full_path)
        full_response = client.create_post(
            caption=full_caption,
            scheduled_at=full_schedule,
            media_url=full_media_url,
            social_accounts=account_ids,
            external_id=make_external_id(automation_id, source_key, "full"),
            skip_processing=skip_processing,
        )
        full_post_id = str(full_response.get("id", "")).strip()
        if not full_post_id:
            die(f"Invalid full post response for {source_key}: {full_response}")

        short_upload_url, short_media_url = client.create_upload_url()
        client.upload_file(short_upload_url, short_path)
        short_response = client.create_post(
            caption=short_caption,
            scheduled_at=short_schedule,
            media_url=short_media_url,
            social_accounts=account_ids,
            external_id=make_external_id(automation_id, source_key, "short"),
            skip_processing=skip_processing,
        )
        short_post_id = str(short_response.get("id", "")).strip()
        if not short_post_id:
            die(f"Invalid short post response for {source_key}: {short_response}")

    automation_items[source_key] = {
        "source_type": source_type,
        "source_id": source_id,
        "source_url": source_url,
        "title": title,
        "full_post_id": full_post_id,
        "short_post_id": short_post_id,
        "full_media_url": full_media_url,
        "short_media_url": short_media_url,
        "full_scheduled_at": full_schedule,
        "short_scheduled_at": short_schedule,
        "updated_at": now_iso(),
        **source_meta,
    }

    return True, f"- `{automation_id}` `{source_key}` scheduled (full `{full_schedule}`, short `{short_schedule}`)"


def run_automations(
    *,
    client: PostForMeClient,
    state: Dict[str, Any],
    config: Dict[str, Any],
    selected_automation_id: str,
    window_mode_override: str,
    last_x_days_override: int,
    specific_date_override: Optional[date],
    max_items_override: int,
    archive_prefix_override: str,
    dry_run: bool,
) -> None:
    defaults = config.get("default_caption_templates", {})
    if not isinstance(defaults, dict):
        defaults = {}
    full_default = str(defaults.get("full_caption", "{title}\n\nSource: {source_url}"))
    short_default = str(defaults.get("short_caption", "{title}\n\nShort clip\nSource: {source_url}\n#shorts"))

    automations = config.get("automations", [])
    if not isinstance(automations, list):
        die("Invalid config: `automations` must be a list")

    state_automations = state.setdefault("automations", {})
    if not isinstance(state_automations, dict):
        state["automations"] = {}
        state_automations = state["automations"]

    total_scheduled = 0
    total_failed = 0
    summary: List[str] = ["## Archive to PostForMe (Multi Automation)"]

    for automation in automations:
        if not isinstance(automation, dict):
            continue
        automation_id = str(automation.get("id", "")).strip()
        if not automation_id:
            continue
        if selected_automation_id and automation_id != selected_automation_id:
            continue
        if not parse_bool(automation.get("enabled", True), True):
            continue

        source_cfg = automation.get("source", {})
        posting_cfg = automation.get("posting", {})
        if not isinstance(source_cfg, dict):
            source_cfg = {}
        if not isinstance(posting_cfg, dict):
            posting_cfg = {}

        auto_state = state_automations.setdefault(automation_id, {"last_run_at": "", "items": {}})
        if not isinstance(auto_state, dict):
            auto_state = {"last_run_at": "", "items": {}}
            state_automations[automation_id] = auto_state
        auto_items = auto_state.setdefault("items", {})
        if not isinstance(auto_items, dict):
            auto_items = {}
            auto_state["items"] = auto_items

        last_run_at = parse_datetime(auto_state.get("last_run_at", ""))
        mode = str(source_cfg.get("selection_mode", "new_since_last_run")).strip().lower()
        if window_mode_override and window_mode_override != "automation":
            mode = window_mode_override
        if mode not in {"new_since_last_run", "last_x_days", "specific_date", "all"}:
            mode = "new_since_last_run"

        last_x_days = parse_int(source_cfg.get("last_x_days", 7), 7)
        if last_x_days_override > 0:
            last_x_days = last_x_days_override

        specific_date = parse_date_only(source_cfg.get("specific_date", ""))
        if specific_date_override:
            specific_date = specific_date_override

        archive_prefix = str(source_cfg.get("archive_prefix", "gp_")).strip() or "gp_"
        if archive_prefix_override:
            archive_prefix = archive_prefix_override

        max_scan_items = parse_int(source_cfg.get("max_archive_scan", 300), 300)
        max_items = parse_int(source_cfg.get("max_items_per_run", 1), 1)
        if max_items_override > 0:
            max_items = max_items_override

        include_archive = parse_bool(source_cfg.get("include_archive", True), True)
        dedupe_scope = str(source_cfg.get("dedupe_scope", "automation")).strip().lower()
        if dedupe_scope not in {"automation", "global"}:
            dedupe_scope = "automation"

        full_offset = parse_int(posting_cfg.get("full_offset_minutes", 20), 20)
        short_offset = parse_int(posting_cfg.get("short_offset_minutes", 80), 80)
        spacing = parse_int(posting_cfg.get("item_spacing_minutes", 240), 240)
        skip_processing = parse_bool(posting_cfg.get("skip_media_processing", False), False)

        full_caption_template = str(posting_cfg.get("full_caption_template", full_default))
        short_caption_template = str(posting_cfg.get("short_caption_template", short_default))

        account_ids_cfg = normalize_list(posting_cfg.get("account_ids", []))
        platforms_cfg = [item.lower() for item in normalize_list(posting_cfg.get("platforms", []))]
        account_ids = resolve_account_ids(client, account_ids_cfg, platforms_cfg)
        if not account_ids:
            die(f"No connected PostForMe accounts found for automation `{automation_id}`")

        candidates: List[Dict[str, Any]] = []
        if include_archive:
            candidates.extend(
                build_archive_candidates(
                    archive_prefix=archive_prefix,
                    max_scan_items=max_scan_items,
                    mode=mode,
                    last_run_at=last_run_at,
                    last_x_days=last_x_days,
                    specific_date=specific_date,
                )
            )

        external_file_value = str(source_cfg.get("external_links_file", "")).strip()
        if external_file_value:
            link_ids = normalize_list(source_cfg.get("external_link_ids", []))
            candidates.extend(
                build_external_candidates(
                    links_file=resolve_repo_path(external_file_value),
                    link_ids=link_ids,
                    mode=mode,
                    last_run_at=last_run_at,
                    last_x_days=last_x_days,
                    specific_date=specific_date,
                )
            )

        candidates.sort(
            key=lambda item: (
                item.get("source_datetime") or datetime(1970, 1, 1, tzinfo=timezone.utc),
                item.get("source_key", ""),
            )
        )

        summary.append(f"### Automation `{automation_id}`")
        summary.append(f"- Mode: `{mode}`")
        summary.append(f"- Accounts targeted: `{len(account_ids)}`")
        summary.append(f"- Candidates discovered: `{len(candidates)}`")

        scheduled = 0
        failed = 0

        for candidate in candidates:
            if scheduled >= max_items:
                break

            source_key = candidate["source_key"]
            if is_record_complete(auto_items.get(source_key)):
                continue

            if dedupe_scope == "global":
                completed_by = completed_in_other_automation(state, automation_id, source_key)
                if completed_by:
                    summary.append(f"- `{source_key}` skipped: already completed by `{completed_by}`")
                    continue

            full_time, short_time = schedule_pair(scheduled, full_offset, short_offset, spacing)

            try:
                changed, message = process_candidate(
                    candidate=candidate,
                    automation_id=automation_id,
                    automation_items=auto_items,
                    client=client,
                    account_ids=account_ids,
                    full_caption_template=full_caption_template,
                    short_caption_template=short_caption_template,
                    full_schedule=full_time,
                    short_schedule=short_time,
                    skip_processing=skip_processing,
                    dry_run=dry_run,
                )
            except Exception as exc:
                changed = False
                message = f"- `{automation_id}` `{source_key}` failed: {exc}"

            print(message)
            summary.append(message)

            if changed:
                scheduled += 1
                total_scheduled += 1
                save_state(state)
            else:
                failed += 1
                total_failed += 1

        auto_state["last_run_at"] = now_iso()
        save_state(state)

        summary.append(f"- Scheduled this run: `{scheduled}`")
        summary.append(f"- Failed this run: `{failed}`")

    summary.append(f"- Dry run: `{str(dry_run).lower()}`")
    summary.append(f"- Total scheduled items: `{total_scheduled}`")
    summary.append(f"- Total failures: `{total_failed}`")
    write_summary(summary)

    print(
        "Summary: "
        f"scheduled_items={total_scheduled}, failures={total_failed}, dry_run={str(dry_run).lower()}"
    )

    if total_scheduled == 0 and total_failed > 0:
        die("No items scheduled and one or more failures occurred.", code=1)


def main() -> None:
    os.chdir(ROOT_DIR)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    api_key = env_required("POSTFORME_API_KEY")
    base_url = env_str("POSTFORME_BASE_URL", "https://api.postforme.dev/v1")
    run_mode = env_str("RUN_MODE", "run").strip().lower()

    client = PostForMeClient(api_key, base_url)

    if run_mode == "list_accounts":
        list_accounts(client)
        return
    if run_mode != "run":
        die(f"Unsupported RUN_MODE: {run_mode}. Use run or list_accounts")

    config_path = resolve_repo_path(env_str("AUTOMATIONS_CONFIG_PATH", str(DEFAULT_AUTOMATION_CONFIG)))
    config = load_json(config_path)
    if not isinstance(config, dict):
        die("Automation config must be a JSON object")

    state = load_state()

    window_override = env_str("WINDOW_MODE_OVERRIDE", "automation").strip().lower()
    if window_override not in {"automation", "new_since_last_run", "last_x_days", "specific_date", "all"}:
        window_override = "automation"

    run_automations(
        client=client,
        state=state,
        config=config,
        selected_automation_id=env_str("AUTOMATION_ID", ""),
        window_mode_override=window_override,
        last_x_days_override=env_int("LAST_X_DAYS_OVERRIDE", 0, minimum=0),
        specific_date_override=parse_date_only(env_str("SPECIFIC_DATE_OVERRIDE", "")),
        max_items_override=env_int("MAX_ITEMS_OVERRIDE", 0, minimum=0),
        archive_prefix_override=env_str("ARCHIVE_PREFIX_OVERRIDE", ""),
        dry_run=env_bool("DRY_RUN", False),
    )


if __name__ == "__main__":
    main()

