# Google Photos -> Archive.org -> YouTube (Full + Short)

Is repo me 2 automations hain:

1. Google Photos Picker se videos uthao, compress karo, Archive.org upload karo  
2. Archive.org se same videos uthao, ek full horizontal aur ek short banao, YouTube par post karo

## Files

```text
.github/workflows/pipeline.yml
.github/workflows/social-publish.yml
scripts/picker_pipeline.py
scripts/social_post_pipeline.py
processed.txt
social_state.json
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

## Important checks

- Agar logs me `Run bash scripts/process.sh` dikhe to old flow chal raha hai.
- Naye setup me `Run python scripts/picker_pipeline.py` aur social ke liye `Run python scripts/social_post_pipeline.py` aana chahiye.

## Notes

- YouTube API quota limit hoti hai; har upload quota use karta hai.
- Social workflow currently YouTube par configured hai (full + short).
