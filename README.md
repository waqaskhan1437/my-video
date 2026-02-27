# Google Photos -> Archive.org -> Social Automations

Is repo me 3 automations hain:

1. Google Photos Picker se videos uthao, compress karo, Archive.org upload karo  
2. Archive.org se full + short banao aur YouTube par post karo  
3. Archive.org/external links se videos process karo aur PostForMe ke zariye multiple social accounts par schedule/post karo

## Files

```text
.github/workflows/pipeline.yml
.github/workflows/social-publish.yml
.github/workflows/archive-postforme.yml
scripts/picker_pipeline.py
scripts/social_post_pipeline.py
scripts/archive_to_postforme.py
automations/postforme_automations.json
automations/external_links.json
processed.txt
social_state.json
postforme_state.json
```

## Flow A: Google Photos -> Archive.org

### Required GitHub secrets

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
- `IA_ACCESS_KEY`
- `IA_SECRET_KEY`

### Run

1. Actions -> `Google Photos to Archive.org` -> `Run workflow`
2. `mode=create_session`
3. Logs se `PICKER_URI` kholo, videos select karo, `Done` karo
4. Workflow dubara run karo: `mode=process_session` + `session_id`

## Flow B: Archive.org -> YouTube (Full + Short)

### Required GitHub secrets

- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

Scope for token:

- `https://www.googleapis.com/auth/youtube.upload`

### Run

1. Actions -> `Archive to Social (YouTube Full + Short)` -> `Run workflow`
2. Inputs:
   - `max_items` (default `1`)
   - `archive_prefix` (default `gp_`)
   - `privacy_status` (`public` / `unlisted` / `private`)

## Flow C: Archive.org + External Links -> PostForMe (Multi Automation)

Ye flow alag hai aur YouTube flow se independent chal sakta hai.

### Required GitHub secrets

- `POSTFORME_API_KEY`

### Automation profiles config

Main config file: `automations/postforme_automations.json`

Har automation profile me aap set kar sakte hain:

- `id` (unique automation name)
- `source.selection_mode`
  - `new_since_last_run`
  - `last_x_days`
  - `specific_date`
  - `all`
- `source.last_x_days`
- `source.specific_date` (`YYYY-MM-DD`)
- `source.archive_prefix`
- `source.external_links_file`
- `posting.account_ids` (per automation custom account IDs)
- `posting.platforms` (fallback filter if account_ids blank)
- offsets and spacing (`full_offset_minutes`, `short_offset_minutes`, `item_spacing_minutes`)

External links file: `automations/external_links.json`

Example external item:

```json
{
  "id": "fiverr-demo-1",
  "enabled": true,
  "url": "https://example.com/video.mp4",
  "title": "Fiverr Portfolio Demo",
  "date": "2026-02-20"
}
```

### Run workflow

1. Actions -> `Archive to PostForMe Multi Automation` -> `Run workflow`
2. `run_mode`:
   - `run`: posts schedule/create karega
   - `list_accounts`: connected PostForMe account IDs show karega
3. Optional overrides:
   - `automation_id`: sirf aik profile chalani ho to
   - `window_mode`: `automation`/`last_x_days`/`specific_date` etc
   - `last_x_days`, `specific_date`
   - `max_items_override`
   - `archive_prefix_override`
   - `dry_run=true` (test mode)

### Daily auto-run

- `archive-postforme.yml` me daily cron configured hai.
- Daily run me state file `postforme_state.json` duplicate posting avoid karta hai.

## Important checks

- Agar logs me `Run bash scripts/process.sh` dikhe to old flow chal raha hai.
- New photos->archive flow logs me `python scripts/picker_pipeline.py` aana chahiye.
- YouTube flow logs me `python scripts/social_post_pipeline.py` aana chahiye.
- PostForMe flow logs me `python scripts/archive_to_postforme.py` aana chahiye.

## Notes

- PostForMe multi-account setup ke liye pehle `run_mode=list_accounts` chala ke account IDs note karein.
- External links ke liye `yt-dlp` workflow me auto install hota hai.
- Agar aap ne secret chat me share kiya hai to security ke liye rotate karna behtar hai.

