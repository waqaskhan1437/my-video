# GitHub Workflows Implementation Plan
**For:** Video Workflow Manager - GitHub Actions Integration
**Created:** February 27, 2026

---

## 📋 OVERVIEW

This plan describes how to create GitHub workflows that will run on GitHub runners (not your local PC) and integrate with your Video Workflow Manager system.

**Key Principle:** All automation runs on GitHub runners → Your local machine stays free for other work.

---

## 🎯 WORKFLOW TYPES

Your system needs 4 main workflows:

### 1. **pipeline.yml** - Google Photos to Archive
- **Purpose:** Sync videos from Google Photos and process them
- **Trigger:** Manual dispatch or scheduled
- **Inputs:** `mode`, `session_id`
- **Runner:** `ubuntu-latest` (GitHub-hosted)
- **Duration:** 5-30 minutes depending on video count

### 2. **social-publish.yml** - Archive to YouTube
- **Purpose:** Upload processed videos to YouTube
- **Trigger:** Manual dispatch or on-demand
- **Inputs:** `max_items`, `privacy_status`
- **Runner:** `ubuntu-latest` (GitHub-hosted)
- **Duration:** 2-10 minutes

### 3. **archive-postforme.yml** - Archive to PostForMe
- **Purpose:** Upload to PostForMe accounts
- **Trigger:** Manual dispatch or scheduled
- **Inputs:** `run_mode`, `automation_id`
- **Runner:** `ubuntu-latest` (GitHub-hosted)
- **Duration:** 5-15 minutes

### 4. **whisper-cpu.yml** - Whisper Transcription (Self-hosted)
- **Purpose:** Generate captions/transcripts using Whisper AI
- **Trigger:** Manual dispatch or scheduled
- **Inputs:** `whisper_model`, `language`, `runner_preference`
- **Runner:** `self-hosted` with label `whisper-cpu`
- **Duration:** 10-60 minutes (depends on video length)
- **Note:** Runs on your dedicated machine, not GitHub servers

---

## 🏗️ STEP-BY-STEP IMPLEMENTATION

### STEP 1: Create Repository Structure

```bash
# If you don't have a GitHub repo yet, create one:
# - Go to github.com/new
# - Name: your-repo-name (e.g., "video-workflow")
# - Add README.md
# - Clone locally

git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name

# Create workflows directory
mkdir -p .github/workflows
```

### STEP 2: Create Workflow Files

All workflow files go in `.github/workflows/` with `.yml` extension.

---

## 📄 WORKFLOW 1: pipeline.yml (Google Photos to Archive)

**File:** `.github/workflows/pipeline.yml`

```yaml
name: Google Photos to Archive

on:
  workflow_dispatch:
    inputs:
      mode:
        description: 'Processing mode'
        required: false
        default: 'process_session'
        type: choice
        options:
          - process_session
          - sync_full
          - process_latest
      session_id:
        description: 'Session ID (optional)'
        required: false
        type: string

jobs:
  archive:
    runs-on: ubuntu-latest
    timeout-minutes: 120

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '7.4'
          extensions: curl, json, pdo_mysql, gd

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg imagemagick

      - name: Trigger automation
        run: |
          # Call your Video Workflow Manager API
          curl -X POST "https://your-domain.com/api/github-automation-trigger.php" \
            -H "Authorization: Bearer ${{ secrets.AUTOMATION_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "action": "archive",
              "mode": "${{ inputs.mode }}",
              "session_id": "${{ inputs.session_id }}",
              "github_run_id": "${{ github.run_id }}",
              "github_run_number": "${{ github.run_number }}"
            }' \
            --max-time 3600

      - name: Check automation status
        if: always()
        run: |
          # Optional: Check if automation completed successfully
          curl -X GET "https://your-domain.com/api/github-automation-status.php" \
            -H "Authorization: Bearer ${{ secrets.AUTOMATION_API_KEY }}" \
            -H "Content-Type: application/json"

      - name: Upload logs to artifacts
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: archive-logs
          path: logs/
          retention-days: 7
```

**Required Secrets for this workflow:**
- `AUTOMATION_API_KEY` - Your API key for authentication

---

## 📄 WORKFLOW 2: social-publish.yml (Archive to YouTube)

**File:** `.github/workflows/social-publish.yml`

```yaml
name: Archive to YouTube

on:
  workflow_dispatch:
    inputs:
      max_items:
        description: 'Maximum videos to upload'
        required: false
        default: '1'
        type: string
      privacy_status:
        description: 'Privacy status for uploads'
        required: false
        default: 'public'
        type: choice
        options:
          - public
          - unlisted
          - private

jobs:
  publish:
    runs-on: ubuntu-latest
    timeout-minutes: 120

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '7.4'
          extensions: curl, json

      - name: Trigger YouTube publishing
        run: |
          curl -X POST "https://your-domain.com/api/github-automation-trigger.php" \
            -H "Authorization: Bearer ${{ secrets.AUTOMATION_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "action": "social",
              "max_items": "${{ inputs.max_items }}",
              "privacy_status": "${{ inputs.privacy_status }}",
              "github_run_id": "${{ github.run_id }}"
            }' \
            --max-time 3600

      - name: Notify on completion
        if: success()
        run: |
          echo "✅ YouTube publishing workflow completed successfully"

      - name: Notify on failure
        if: failure()
        run: |
          echo "❌ YouTube publishing workflow failed"
          exit 1
```

**Required Secrets:**
- `AUTOMATION_API_KEY` - Your API key

---

## 📄 WORKFLOW 3: archive-postforme.yml (PostForMe Automation)

**File:** `.github/workflows/archive-postforme.yml`

```yaml
name: Archive to PostForMe

on:
  workflow_dispatch:
    inputs:
      run_mode:
        description: 'Run mode'
        required: false
        default: 'run'
        type: choice
        options:
          - run
          - test
          - dry-run
      automation_id:
        description: 'Automation ID'
        required: false
        default: 'daily_archive_accounts_a'
        type: string

jobs:
  postforme:
    runs-on: ubuntu-latest
    timeout-minutes: 120

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '7.4'
          extensions: curl, json

      - name: Trigger PostForMe automation
        run: |
          curl -X POST "https://your-domain.com/api/github-automation-trigger.php" \
            -H "Authorization: Bearer ${{ secrets.AUTOMATION_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "action": "postforme",
              "run_mode": "${{ inputs.run_mode }}",
              "automation_id": "${{ inputs.automation_id }}",
              "github_run_id": "${{ github.run_id }}"
            }' \
            --max-time 3600

      - name: Log results
        if: always()
        run: |
          curl -X GET "https://your-domain.com/api/github-automation-status.php?run_id=${{ github.run_id }}" \
            -H "Authorization: Bearer ${{ secrets.AUTOMATION_API_KEY }}"
```

**Required Secrets:**
- `AUTOMATION_API_KEY` - Your API key

---

## 📄 WORKFLOW 4: whisper-cpu.yml (Self-hosted Transcription)

**File:** `.github/workflows/whisper-cpu.yml`

```yaml
name: Whisper CPU Job

on:
  workflow_dispatch:
    inputs:
      whisper_model:
        description: 'Whisper model size'
        required: false
        default: 'base'
        type: choice
        options:
          - tiny
          - base
          - small
          - medium
          - large
      language:
        description: 'Language for transcription'
        required: false
        default: 'auto'
        type: string
      runner_preference:
        description: 'Runner type'
        required: false
        default: 'self-hosted'
        type: choice
        options:
          - self-hosted
          - github-hosted

jobs:
  whisper:
    # This runs on self-hosted runners with label "whisper-cpu"
    runs-on: [self-hosted, whisper-cpu]
    timeout-minutes: 180

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Check system info
        run: |
          echo "OS: $(uname -a)"
          echo "CPU: $(nproc) cores"
          echo "Memory: $(free -h | grep Mem)"
          if command -v nvidia-smi &> /dev/null; then
            echo "GPU: Available"
            nvidia-smi
          else
            echo "GPU: Not available"
          fi

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install Whisper
        run: |
          pip install --upgrade pip
          pip install openai-whisper

      - name: Trigger Whisper transcription
        run: |
          curl -X POST "https://your-domain.com/api/github-automation-trigger.php" \
            -H "Authorization: Bearer ${{ secrets.AUTOMATION_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "action": "whisper",
              "whisper_model": "${{ inputs.whisper_model }}",
              "language": "${{ inputs.language }}",
              "runner_preference": "${{ inputs.runner_preference }}",
              "github_run_id": "${{ github.run_id }}"
            }' \
            --max-time 3600

      - name: Upload transcription logs
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: whisper-logs
          path: logs/
          retention-days: 7
```

**Required Secrets:**
- `AUTOMATION_API_KEY` - Your API key

**Special Requirements:**
- Must run on self-hosted runner labeled `whisper-cpu`
- Runner must have Python 3.9+ installed
- GPU support optional but recommended for faster transcription

---

## 🔐 STEP 3: Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AUTOMATION_API_KEY` | Your API key | For authentication |
| `WEBHOOK_URL` | Your webhook URL | For notifications (optional) |

**Example API Key Format:**
```
ghp_abc123def456ghi789jkl012mno345pqr678
```

---

## 🤖 STEP 4: Create Backend API Endpoint

Your workflows will call this endpoint. Create: `/api/github-automation-trigger.php`

```php
<?php
declare(strict_types=1);

require_once __DIR__ . '/../config.php';

header('Content-Type: application/json');

// Verify API key
$apiKey = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
$apiKey = str_replace('Bearer ', '', $apiKey);

if ($apiKey !== getenv('AUTOMATION_API_KEY')) {
    http_response_code(401);
    echo json_encode(['ok' => false, 'error' => 'Unauthorized']);
    exit;
}

// Get payload
$payload = json_decode(file_get_contents('php://input'), true);
$action = $payload['action'] ?? '';

try {
    switch ($action) {
        case 'archive':
            // Call archive automation
            triggerArchiveAutomation($payload);
            break;

        case 'social':
            // Call social publishing
            triggerSocialAutomation($payload);
            break;

        case 'postforme':
            // Call PostForMe automation
            triggerPostForMeAutomation($payload);
            break;

        case 'whisper':
            // Call Whisper transcription
            triggerWhisperAutomation($payload);
            break;

        default:
            http_response_code(400);
            echo json_encode(['ok' => false, 'error' => 'Invalid action']);
            exit;
    }

    http_response_code(200);
    echo json_encode([
        'ok' => true,
        'message' => "Automation '$action' triggered",
        'github_run_id' => $payload['github_run_id'] ?? null
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => $e->getMessage()]);
}

function triggerArchiveAutomation($payload) {
    // Your existing automation.php logic here
    // Or call via HTTP: file_get_contents('http://localhost/automation.php?action=...');
}

function triggerSocialAutomation($payload) {
    // YouTube publishing logic
}

function triggerPostForMeAutomation($payload) {
    // PostForMe automation logic
}

function triggerWhisperAutomation($payload) {
    // Whisper transcription logic
}
```

---

## 📤 STEP 5: Push to GitHub

```bash
# Add all workflow files
git add .github/workflows/*.yml

# Commit changes
git commit -m "Add GitHub Actions workflows"

# Push to repository
git push origin main
```

After pushing, your workflows will appear in GitHub Actions tab automatically.

---

## ✅ STEP 6: Test Workflows

### In GitHub UI:
1. Go to **Actions** tab in your repo
2. Select workflow (e.g., "Google Photos to Archive")
3. Click **Run workflow**
4. Fill in input parameters
5. Click **Run**
6. Monitor execution in real-time

### From Your Dashboard:
1. Go to `github-automation.php` page
2. Click **Refresh Status** button
3. You should see the workflow run appear
4. Click **Run** button for any workflow
5. Check logs and status

---

## 🔧 STEP 7: Set Up Self-Hosted Runner (For Whisper Only)

Only needed if you want to run Whisper transcription.

### On Your Computer:

```bash
# 1. Go to your repo > Settings > Actions > Runners > New self-hosted runner

# 2. Download runner software
cd ~/github-runner
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# 3. Configure runner
./config.sh --url https://github.com/yourusername/your-repo --token YOUR_TOKEN

# 4. Run as service (optional)
sudo ./svc.sh install
sudo ./svc.sh start

# 5. Or run manually
./run.sh
```

### Runner will be labeled: `self-hosted`
### Add custom label: `whisper-cpu` during setup

---

## 📊 WORKFLOW EXECUTION FLOW

```
┌─────────────────────────────────────────┐
│   You Click "Run" in github-automation  │
│              (UI Dashboard)              │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  api/github-actions.php                 │
│  (Dispatch workflow request to GitHub)  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  GitHub Actions API                     │
│  (Receives dispatch request)            │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  GitHub Runner (Linux VM)               │
│  .github/workflows/pipeline.yml         │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Calls Your API:                        │
│  api/github-automation-trigger.php      │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Your Automation Logic                  │
│  (automation.php / your code)           │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Results appear in GitHub Actions       │
│  Dashboard + Your UI                    │
└─────────────────────────────────────────┘
```

---

## ⚠️ IMPORTANT NOTES

### For GitHub-Hosted Runners (ubuntu-latest):
- ✅ Runs on GitHub's servers (free tier: 2,000 minutes/month)
- ✅ No setup required
- ❌ Cannot access your local files
- ❌ Cannot run GPU-heavy tasks efficiently
- ✅ Great for: API calls, video uploads, database operations

### For Self-Hosted Runners (whisper-cpu):
- ✅ Runs on your machine
- ✅ Can access local resources
- ✅ Can use GPU if available
- ❌ Your machine must stay online
- ❌ More setup required
- ✅ Best for: CPU/GPU intensive tasks like transcription

---

## 🐛 TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| Workflows not visible in GitHub Actions | Push to repo, then refresh page (F5) |
| "Invalid token" error | Check GitHub token in settings, re-enter if needed |
| Workflow fails to run | Check API endpoint URL, verify AUTOMATION_API_KEY |
| Self-hosted runner offline | Make sure `./run.sh` is running on your machine |
| Rate limit exceeded | GitHub has limits - wait or use larger runner |
| Long workflow timeout | Increase `timeout-minutes` in YAML file |

---

## 📝 NEXT STEPS

1. ✅ Create `.github/workflows/` directory
2. ✅ Create all 4 workflow YAML files
3. ✅ Push to GitHub
4. ✅ Configure GitHub secrets
5. ✅ Create backend API endpoint (`github-automation-trigger.php`)
6. ✅ Test each workflow from GitHub UI
7. ✅ Test dispatch from your dashboard
8. ⚠️ Set up self-hosted runner (optional, for Whisper only)
9. ✅ Monitor first few runs
10. ✅ Document any custom logic

---

## 📞 SUPPORT RESOURCES

- **GitHub Workflows Documentation**: https://docs.github.com/en/actions/using-workflows
- **Workflow Syntax**: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions
- **GitHub API**: https://docs.github.com/en/rest/actions
- **Self-Hosted Runners**: https://docs.github.com/en/actions/hosting-your-own-runners

---

**Last Updated:** 2026-02-27
**Status:** Ready for Implementation
**Difficulty:** Intermediate (2-4 hours)
