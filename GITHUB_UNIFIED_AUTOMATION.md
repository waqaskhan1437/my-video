# GitHub Unified Automation Runner

## 🎯 Overview

Your automation now runs on GitHub runners instead of your local PC! The system uses a **single unified workflow** that executes your complete automation process on GitHub's servers.

**Key Difference from Before:**
- ❌ OLD: Separate workflows for pipeline, social, whisper, postforme
- ✅ NEW: One unified `automation.yml` that runs YOUR automation with YOUR settings

## 📋 How It Works

### 1. **User Enables GitHub Runner**
```
Dashboard → Edit Automation → Check "GitHub Actions Runner" → Save
```

### 2. **User Clicks Run**
```
Dashboard → Run Automation (with GitHub checkbox enabled)
```

### 3. **System Dispatch Process**
```
Local PC (run-sync.php)
    ↓
Checks: github_runner_enabled = true?
    ↓
Sends automation_id to GitHub API
    ↓
GitHub Actions (automation.yml)
    ↓
Fetches automation config via API
    ↓
Runs complete automation process
    ↓
Sends completion notification back
```

## 🔄 Complete Automation Flow on GitHub

### Step 1: Configuration Fetch
```bash
GET /api/get-automation-config.php?automation_id=123
```
Returns:
- Automation settings (video source, editing options, posting config)
- API key credentials
- FTP configuration
- PostForMe account details

### Step 2: Automation Execution
```bash
POST /api/github-run-automation.php
```
Workflow receives JSON with entire config and:

1. **Fetches Videos**
   - Manual URLs: Downloads from provided links
   - FTP: Connects using credentials, downloads from storage

2. **Applies Filters**
   - Date range filter (start_date to end_date)
   - Days filter (last X days)

3. **Edits Videos**
   - Trims to duration (e.g., 60 seconds)
   - Applies aspect ratio (e.g., 9:16 for short-form)
   - Adds text overlays (branding text top/bottom)

4. **Posts to Platforms**
   - YouTube: Uses youtube_api_key from your settings
   - TikTok: Uses tiktok_access_token
   - Instagram: Uses instagram_access_token
   - PostForMe: Uses configured accounts

5. **Schedules Posts**
   - If PostForMe enabled: Schedules for later
   - Otherwise: Posts immediately

### Step 3: Completion Notification
```bash
POST /api/github-automation-complete.php
```
Logs:
- Workflow run ID
- Conclusion (success/failure)
- Completion timestamp
- GitHub Actions URL

## 📁 New/Modified Files

### New Workflow
- **`.github/workflows/automation.yml`** - Single unified runner for all automations

### New API Endpoints
- **`api/get-automation-config.php`** - Returns automation configuration for GitHub
- **`api/github-run-automation.php`** - Executes automation with provided config
- **`api/github-automation-complete.php`** - Logs workflow completion

### Modified Files
- **`api/run-sync.php`** - Updated dispatch logic to send automation_id instead of fixed workflows
- **`automation.php`** - Updated UI to show unified runner instead of multiple workflows

## 🔑 Database Columns

Two columns added to `automation_settings`:
- `github_runner_enabled` (TINYINT(1)) - Toggle GitHub runner on/off
- `github_workflow` (VARCHAR(50)) - Always "unified" for new system

## ⚙️ Configuration Requirements

For GitHub runner to work, you need:

### 1. GitHub Repository Secrets (in Settings → Secrets)
```
AUTOMATION_API_KEY      = Your API key for authentication
WORKFLOW_API_ENDPOINT   = http://your-domain.com/video-workflow-edit-enabled
```

### 2. GitHub Settings (github-automation.php)
- GitHub Actions Enabled: ✅
- API Token: Personal access token with repo access
- Repo Owner: waqaskhan1437
- Repo Name: my-video
- Branch: main

### 3. Your Automation Settings
- Video Source: FTP or Manual URLs
- Editing Options: Duration, aspect ratio, text overlays
- Posting Platforms: YouTube, TikTok, Instagram, PostForMe
- Schedules: When to run (daily, every X minutes, etc.)

## 🎬 Example Workflow

### Your Automation Configuration:
```
Name: "Short-Form Daily"
Video Source: FTP (Bunny CDN)
Filter: Last 7 days
Duration: 60 seconds
Aspect Ratio: 9:16 (TikTok/Reels)
Branding: Top="Logo", Bottom="@YourChannel"
YouTube: Enabled
PostForMe: Enabled with 3 accounts
Schedule: Daily at 9 AM
GitHub Runner: ✅ Enabled
```

### What Happens on GitHub:
1. ⏰ Scheduler triggers at 9 AM
2. 🎥 Fetches last 7 days of videos from FTP
3. ✂️ Edits to 60 seconds, 9:16 aspect ratio
4. 🔤 Adds text branding
5. 📤 Uploads to YouTube
6. 📅 Schedules to PostForMe for later posting
7. ✅ Completes with 0 impact on your PC

## 💡 Key Benefits

| Feature | Local | GitHub Runner |
|---------|-------|---------------|
| Requires PC always on | ✅ | ❌ |
| Bandwidth usage | Heavy | None from PC |
| Processing power | Uses your CPU | Uses GitHub servers |
| Cost | Your electricity | Free (GitHub Actions) |
| Reliability | Subject to crashes | Always available |
| Scheduling | Requires Windows Task Scheduler | Built-in cron |

## 🔍 Monitoring

### Check Status:
1. **Local Dashboard**: Shows automation status, last run time, results
2. **GitHub Actions**: `https://github.com/waqaskhan1437/my-video/actions`
   - See live logs of each step
   - Download artifacts (videos, logs)
   - Retry failed runs

### View Logs:
```
GitHub Actions → automation.yml → Latest Run → Logs
```

Shows:
- Video fetch progress
- Editing process
- Posting results
- Any errors

## 🚀 Usage

### Enable for an Automation:
```
1. Dashboard → Automations
2. Click Edit on automation
3. Check "GitHub Actions Runner"
4. Save
5. Next scheduled run will use GitHub
```

### Disable (Back to Local):
```
1. Dashboard → Automations
2. Click Edit on automation
3. Uncheck "GitHub Actions Runner"
4. Save
5. Next run uses local PC
```

### Manual Trigger on GitHub:
```
GitHub → Actions → automation → Run workflow
→ Enter automation_id → Run
```

## ⚠️ Troubleshooting

### Workflow Not Triggering
- [ ] Check GitHub Actions are enabled in github-automation.php
- [ ] Verify AUTOMATION_API_KEY secret is set
- [ ] Check WORKFLOW_API_ENDPOINT secret is correct

### Workflow Failing
- [ ] Check logs in GitHub Actions
- [ ] Verify automation configuration is valid
- [ ] Check FTP credentials if using FTP source
- [ ] Verify video source has files

### API Endpoints Not Found
- [ ] Ensure all 3 new API files are created:
  - `api/get-automation-config.php`
  - `api/github-run-automation.php`
  - `api/github-automation-complete.php`
- [ ] Verify file permissions allow PHP execution

### Database Connection Error
- [ ] GitHub runner must reach your database from internet
- [ ] Ensure database is publicly accessible (carefully!)
- [ ] Or run database sync before workflow (fetch backups)

## 📊 Statistics & Performance

- **Average Run Time**: Depends on video count and editing
- **Bandwidth**: All downloaded to GitHub servers, no PC impact
- **Cost**: Free (GitHub Actions has generous free tier)
- **Concurrency**: Can run multiple automations in parallel

## 🔐 Security Notes

1. **API Key**: Stored as GitHub secret, never exposed in logs
2. **Database**: Use separate read-only user if possible
3. **FTP Credentials**: Stored in database, transmitted via HTTPS
4. **Artifacts**: Videos uploaded to GitHub, stored for 30 days

## 📝 Database Schema

```sql
ALTER TABLE automation_settings ADD COLUMN
  github_runner_enabled TINYINT(1) DEFAULT 0,
  github_workflow VARCHAR(50) NULL;

-- Example data
INSERT INTO automation_settings (name, github_runner_enabled, github_workflow)
VALUES ('My Automation', 1, 'unified');
```

## 🎯 Next Steps

1. ✅ Database columns added
2. ✅ New API endpoints created
3. ✅ Unified workflow deployed
4. ✅ Dispatch logic updated
5. ✅ UI simplified

### To Use:
1. Go to GitHub Automation Settings (github-automation.php)
2. Enable GitHub Actions and add credentials
3. Edit an automation
4. Check "GitHub Actions Runner"
5. Next run will execute on GitHub!

---

**Automation ID for GitHub**: Passed automatically from dashboard when you click "Run"

**Questions?** Check the logs in GitHub Actions for detailed error messages.
