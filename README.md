# Google Photos -> Compress -> Archive.org (Free, Server-to-Server)

Ye starter setup GitHub Actions par chalta hai:

1. `links.txt` se Google Photos links read karta hai  
2. `yt-dlp` se video download karta hai (runner par, local PC par nahi)  
3. `ffmpeg` se compress karta hai  
4. `archive.org` par `ia` CLI se upload karta hai  
5. `processed.txt` update karke duplicate processing avoid karta hai

Important:

- Google Photos policies/links ki wajah se direct shared links kabhi fail ho sakte hain.
- Agar link private ho to cookies chahiye hongi.
- Sab process GitHub runner par hota hai, aapke laptop par nahi.
- Agar log me `Unsupported URL: https://photos.google.com/share/...` aaye to us link ko tool read nahi kar pa raha.

## Google Photos link unsupported ho to kya karein

1. Best reliable path: videos ko Google Drive ya kisi direct-file source me rakho, phir woh links use karo.
2. Ya Google Photos ka manual export (Takeout/download) karke source update karo.
3. Workflow ab summary print karta hai aur agar upload 0 ho to run fail karega (red), taake false-success na aaye.

## 1) One-time setup

1. GitHub par new **public** repo banao aur ye files upload karo.
2. Archive.org account banao aur S3 keys nikaalo: `https://archive.org/account/s3.php`
3. Repo Settings -> Secrets and variables -> Actions -> New repository secret:
   - `IA_ACCESS_KEY`
   - `IA_SECRET_KEY`
   - Optional: `GPHOTOS_COOKIES` (Netscape cookies.txt format)
4. `links.txt` me har line par 1 video link daalo.
5. Actions tab se workflow run karo.

## 2) File structure

```text
.github/workflows/pipeline.yml
scripts/process.sh
links.txt
processed.txt
```

## 3) Notes

- Public repo me standard GitHub-hosted runners free hote hain.
- Ek job max 6 ghante chal sakti hai.
- Bohat bari files/batch ho to links ko chunks me daalo.
