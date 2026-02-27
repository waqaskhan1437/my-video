# Google Photos -> Archive.org -> Social Automations

Is repo me 3 automations hain:

1. Google Photos Picker se videos uthao, compress karo, Archive.org upload karo  
2. Archive.org se same videos uthao, ek full horizontal aur ek short banao, YouTube par post karo  
3. Archive.org se videos process karo aur PostForMe ke zariye social accounts par schedule/post karo (daily)

## Files

```text
.github/workflows/pipeline.yml
.github/workflows/social-publish.yml
.github/workflows/archive-postforme.yml
scripts/picker_pipeline.py
scripts/social_post_pipeline.py
scripts/archive_to_postforme.py
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
3. Workflow:
   - Archive item download karta hai
   - Full horizontal (16:9) generate karta hai
   - Short vertical (9:16, 59s) generate karta hai
   - Dono YouTube par upload karta hai
   - `social_state.json` me progress save karta hai

## Flow C: Archive.org -> PostForMe (Daily)

Ye flow alag hai aur YouTube flow se independent chal sakta hai.

### Required GitHub secrets

- `POSTFORME_API_KEY`

### Run

1. Actions -> `Archive to PostForMe Daily` -> `Run workflow`
2. Inputs:
   - `max_items` (default `1`)
   - `archive_prefix` (default `gp_`)
   - `platforms` (optional, comma separated, e.g. `instagram,facebook`)
   - `full_offset_minutes` (default `20`)
   - `short_offset_minutes` (default `80`)
   - `item_spacing_minutes` (default `240`)
3. Workflow:
   - Archive se new source video fetch karta hai
   - Full horizontal + short vertical generate karta hai
   - Processed files PostForMe media me upload karta hai
   - PostForMe `/social-posts` par scheduled posts create karta hai
   - `postforme_state.json` me progress save karta hai

### Daily auto-run

- Is workflow me daily cron already configured hai.
- Daily run sirf new archive items ko process karega.

## Important checks

- Agar logs me `Run bash scripts/process.sh` dikhe to old flow chal raha hai.
- Naye setup me `Run python scripts/picker_pipeline.py` aur social ke liye `Run python scripts/social_post_pipeline.py` aana chahiye.
- PostForMe flow ke liye logs me `Run python scripts/archive_to_postforme.py` aana chahiye.

## Notes

- YouTube API quota limit hoti hai; har upload quota use karta hai.
- PostForMe automation `postforme_state.json` ki base par duplicate schedule avoid karta hai.
