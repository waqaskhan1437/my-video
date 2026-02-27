# Google Photos Picker -> Compress -> Archive.org (Free on GitHub Actions)

Ye setup Google Photos **shared link** par depend nahi karta.  
Isme Google Photos Picker API use hoti hai:

1. Session create hoti hai  
2. Aap picker URL me videos select karte ho  
3. Workflow selected videos download + compress + archive.org upload karta hai

## Why this works

- Direct `photos.app.goo.gl` links mostly automation-friendly nahi hotay.
- Picker API official flow hai jahan user selection required hoti hai.

## Files

```text
.github/workflows/pipeline.yml
scripts/picker_pipeline.py
processed.txt
```

## Migration check (important)

- Agar run logs me `Run bash scripts/process.sh` dikhe, to aap abhi old workflow chala rahe ho.
- Naye setup me logs me `Run python scripts/picker_pipeline.py` aana chahiye.

## One-time setup

1. Archive.org account me S3 keys banao: `https://archive.org/account/s3.php`
2. Google Cloud me project banao.
3. Google Photos Picker API enable karo.
4. OAuth consent screen configure karo (test user me apna Gmail add karo).
5. OAuth client credentials banao (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`).
6. Refresh token lo (scope: `https://www.googleapis.com/auth/photospicker.mediaitems.readonly`).
   - Easy method: OAuth Playground with your own client credentials.

## GitHub Secrets

Repo -> Settings -> Secrets and variables -> Actions:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
- `IA_ACCESS_KEY`
- `IA_SECRET_KEY`

## Run flow

### Step A: Create picker session

1. Actions -> `Google Photos to Archive.org` -> `Run workflow`
2. `mode` = `create_session`
3. Run logs/summary se `Session ID` aur `Picker URL` copy karo
4. Picker URL kholo, videos select karo, `Done` karo

### Step B: Process selected videos

1. Same workflow dubara run karo
2. `mode` = `process_session`
3. `session_id` me Step A wala session id paste karo
4. Workflow:
   - selected videos download karega
   - ffmpeg se compress karega
   - archive.org par upload karega
   - `processed.txt` me processed item IDs save karega

## Notes

- Process session run me `IA_*` secrets required hain.
- Agar selected item video nahi hai to skip hoga.
- Agar attempts hue lekin upload 0 raha, run fail (red) karega.
- Session ID agar `sessions/...` form me ho to bhi script usay handle kar leti hai.
