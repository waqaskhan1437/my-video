# GitHub Automation - Quick Start Guide

**Time Required:** 30-60 minutes
**Difficulty:** Beginner-Friendly
**No Local PC Usage:** All runs on GitHub's servers

---

## ⚡ QUICK SUMMARY

| What | Where | Who Runs |
|------|-------|----------|
| **UI Dashboard** | `/github-automation.php` | Your PC (one-time click) |
| **Actual Work** | GitHub Runners | GitHub's Servers (free) |
| **Your PC** | Does Nothing | Stays Free for Other Work ✅ |

---

## 📋 CHECKLIST (Copy-Paste Ready)

### Phase 1: GitHub Repository (10 mins)
- [ ] Have GitHub account? → https://github.com/signup
- [ ] Have repository? → https://github.com/new
- [ ] Clone locally: `git clone https://github.com/YOUR_USERNAME/YOUR_REPO`
- [ ] Go into folder: `cd YOUR_REPO`

### Phase 2: Create Workflows (10 mins)
```bash
# Run these commands in your repo folder:

mkdir -p .github/workflows

# Copy 4 workflow files from:
# GITHUB_WORKFLOWS_IMPLEMENTATION_PLAN.md
# Files: pipeline.yml, social-publish.yml, archive-postforme.yml, whisper-cpu.yml

git add .github/workflows/
git commit -m "Add GitHub Actions workflows"
git push origin main
```

### Phase 3: Configure GitHub (5 mins)
1. Go to: `GitHub Repo > Settings > Secrets and variables > Actions`
2. Click: **New repository secret**
3. Add: `AUTOMATION_API_KEY` = (your API key)

### Phase 4: Verify in GitHub UI (5 mins)
1. Go to: `GitHub Repo > Actions` tab
2. See 4 workflows? ✅ Done!
3. Click any workflow → Click **Run workflow**

### Phase 5: Connect to Your Dashboard (5 mins)
1. Go to: Your domain → `github-automation.php`
2. Fill in:
   - [ ] **Repo Owner:** (your username)
   - [ ] **Repo Name:** (your repo name)
   - [ ] **GitHub Token:** (from https://github.com/settings/tokens)
   - [ ] **Enable:** Check the box
3. Click: **Save Settings**
4. Click: **Refresh Status**

### Phase 6: First Test (5 mins)
1. In dashboard, scroll down to **Quick Dispatch**
2. Click: **Run** for any workflow
3. Wait 30 seconds
4. Check logs appear in table ✅

---

## 🎯 WHAT EACH WORKFLOW DOES

### 1. **Google Photos to Archive** 🟦
- **What:** Downloads from Google Photos, processes videos
- **Time:** 5-30 min
- **Runner:** GitHub servers (free)
- **Runs on:** ubuntu-latest
- **Test Inputs:** Leave empty or use defaults

### 2. **Archive to YouTube** 🟥
- **What:** Uploads processed videos to YouTube
- **Time:** 2-10 min
- **Runner:** GitHub servers (free)
- **Runs on:** ubuntu-latest
- **Test Inputs:** max_items=1, privacy=public

### 3. **Archive to PostForMe** 🟪
- **What:** Sends videos to PostForMe accounts
- **Time:** 5-15 min
- **Runner:** GitHub servers (free)
- **Runs on:** ubuntu-latest
- **Test Inputs:** Leave empty (uses defaults)

### 4. **Whisper CPU Job** 🟨
- **What:** Generates captions using AI (Whisper)
- **Time:** 10-60 min
- **Runner:** Your machine (self-hosted) - Optional
- **Runs on:** self-hosted (if available)
- **Test Inputs:** model=base, language=auto

---

## 🔑 HOW TO GET GITHUB TOKEN

### Quick Steps:
1. Go to: https://github.com/settings/tokens
2. Click: **Generate new token (classic)**
3. Select scopes:
   - ✅ `repo` (full control)
   - ✅ `workflow` (manage actions)
4. Click: **Generate token**
5. Copy token (won't show again!) 🔐
6. Paste in dashboard settings

### Fine-Grained Token (Safer):
1. Go to: https://github.com/settings/personal-access-tokens/new
2. Name: `VideoWorkflow`
3. Expiration: 90 days or custom
4. Repository access: Your repo only
5. Permissions:
   - Actions: Read & write
   - Contents: Read-only
6. Generate & copy

---

## 📊 MONITORING YOUR WORKFLOWS

### In Your Dashboard:
```
URL: /github-automation.php

Dashboard shows:
- 📊 Total workflows
- ⏱️ Running/queued jobs
- ✅ Self-hosted runners online
- ❌ Failed jobs in 24h
```

### In GitHub UI:
```
URL: github.com/YOUR_USERNAME/YOUR_REPO/actions

Shows:
- Live workflow runs
- Detailed logs
- Status (✅ success, ❌ failed, ⏱️ running)
- Time taken
```

### View Logs:
1. Click workflow run
2. Click job name
3. See live output
4. Download artifacts (if any)

---

## 🚨 COMMON ISSUES

| Problem | Fix |
|---------|-----|
| Can't see workflows in GitHub | Push again, wait 30s, refresh browser |
| "API token invalid" | Generate new token, make sure you copied all characters |
| Workflow fails immediately | Check API endpoint URL in workflow YAML |
| No GitHub connection in dashboard | Verify token, repo owner, repo name are correct |
| Workflows run but do nothing | Check `api/github-automation-trigger.php` exists and API key matches |

---

## 💾 FILE LOCATIONS

### On Your Server:
```
project-root/
├── .github/
│   └── workflows/
│       ├── pipeline.yml
│       ├── social-publish.yml
│       ├── archive-postforme.yml
│       └── whisper-cpu.yml
├── api/
│   ├── github-actions.php (✅ exists)
│   └── github-automation-trigger.php (⚠️ create this)
├── includes/
│   └── GitHubActionsAPI.php (✅ exists)
└── github-automation.php (✅ exists - your dashboard)
```

### On GitHub:
```
github.com/USERNAME/REPO/
├── .github/workflows/
│   └── (same 4 files as above)
├── (any other files)
```

---

## 🔄 EXECUTION FLOW

```
1. You Click "Run"
   └─> github-automation.php

2. Dashboard Calls GitHub API
   └─> api/github-actions.php

3. GitHub Receives Request
   └─> Starts runner (ubuntu-latest or self-hosted)

4. Runner Executes Workflow
   └─> .github/workflows/XXX.yml

5. Workflow Calls Your API
   └─> api/github-automation-trigger.php

6. Your Server Does Work
   └─> automation.php or your code

7. Results Appear
   └─> GitHub Actions dashboard + Your dashboard
```

---

## 📈 PRICING

### GitHub-Hosted Runners:
| Plan | Free Quota | Cost After |
|------|-----------|-----------|
| Free | 2,000 min/month | $0.25/min |
| Pro | 3,000 min/month | $0.25/min |
| Enterprise | 50,000 min/month | $0.25/min |

**Note:** Most small automation uses ~100-500 min/month (plenty of free quota)

### Self-Hosted Runners:
- **Cost:** Free (uses your hardware)
- **Setup:** ~30 minutes first time
- **Best for:** Whisper AI (heavy CPU/GPU)

---

## ✅ VALIDATION CHECKLIST

After setup, verify:

- [ ] Can see 4 workflows in GitHub Actions tab
- [ ] Can click "Run workflow" for any workflow
- [ ] Dashboard shows "Configured" status
- [ ] Recent runs appear in dashboard table
- [ ] Can view logs by clicking run
- [ ] API endpoint working (check GitHub Actions logs)

---

## 🆘 NEED HELP?

### Check These:
1. **GitHub Actions Docs**: https://docs.github.com/en/actions
2. **API Reference**: https://docs.github.com/en/rest/actions
3. **Workflow Syntax**: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions

### Your Documentation:
1. `GITHUB_AUTOMATION_AUDIT.md` - Full technical audit
2. `GITHUB_WORKFLOWS_IMPLEMENTATION_PLAN.md` - Detailed workflow guide
3. `AUTOMATION_SETUP_GUIDE.md` - Your existing automation docs

---

## 🎓 LEARNING RESOURCES

- Video: GitHub Actions 101 → https://www.youtube.com/results?search_query=github+actions+tutorial
- Docs: Self-hosted runners → https://docs.github.com/en/actions/hosting-your-own-runners
- Examples: Workflow samples → https://github.com/actions/starter-workflows

---

## 🚀 NEXT STEPS

```
1. Create .github/workflows/ directory
2. Add 4 workflow YAML files
3. Push to GitHub
4. Configure GitHub secrets
5. Test in GitHub UI
6. Connect dashboard
7. Run first workflow
8. Monitor in dashboard
9. Set up self-hosted runner (optional)
10. Done! ✅
```

**Estimated Time:** 1 hour total
**Difficulty:** Beginner-Friendly
**Result:** Automated workflows running on GitHub (your PC stays free!)

---

**Last Updated:** 2026-02-27
**Version:** 1.0 - Quick Start
