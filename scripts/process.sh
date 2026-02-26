#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

touch links.txt processed.txt
mkdir -p tmp/input tmp/output

mapfile -t LINKS < <(grep -vE '^\s*$|^\s*#' links.txt || true)

if [ "${#LINKS[@]}" -eq 0 ]; then
  echo "No links found in links.txt"
  exit 0
fi

for raw_url in "${LINKS[@]}"; do
  url="$(echo "${raw_url}" | sed 's/[[:space:]]*$//')"
  if [ -z "${url}" ]; then
    continue
  fi

  if grep -Fxq "${url}" processed.txt; then
    echo "Skipping already processed URL."
    continue
  fi

  hash="$(printf '%s' "${url}" | sha1sum | awk '{print substr($1,1,12)}')"
  identifier="gp_${hash}_$(date -u +%Y%m%d%H%M%S)"

  rm -rf tmp/input/* tmp/output/*

  echo "Downloading: ${url}"
  cookie_args=()
  if [ -s cookies.txt ]; then
    cookie_args=(--cookies cookies.txt)
  fi

  if ! yt-dlp \
    --no-playlist \
    "${cookie_args[@]}" \
    --output "tmp/input/source.%(ext)s" \
    "${url}"; then
    echo "Download failed, continuing next URL."
    continue
  fi

  input_file="$(find tmp/input -maxdepth 1 -type f | head -n 1 || true)"
  if [ -z "${input_file}" ]; then
    echo "No source file found after download."
    continue
  fi

  echo "Compressing: ${input_file}"
  if ! ffmpeg -y -i "${input_file}" \
    -vf "scale='min(1280,iw)':-2" \
    -c:v libx264 -preset veryfast -crf 28 \
    -c:a aac -b:a 96k \
    -movflags +faststart \
    "tmp/output/video.mp4"; then
    echo "Compression failed, continuing next URL."
    continue
  fi

  if [ ! -f "tmp/output/video.mp4" ]; then
    echo "Compressed output missing, continuing."
    continue
  fi

  echo "Uploading to archive.org item: ${identifier}"
  if ! ia upload "${identifier}" "tmp/output/video.mp4" \
    --metadata="title:${identifier}" \
    --metadata="mediatype:movies" \
    --metadata="source:google-photos-link" \
    --retries=5; then
    echo "Upload failed, continuing next URL."
    continue
  fi

  echo "${url}" >> processed.txt
  echo "Uploaded: https://archive.org/details/${identifier}"
done

echo "Pipeline completed."
