# GitHub API Token Setup

## ❌ Current Error
```
"GitHub Actions not configured. Please configure it in GitHub Automation settings first."
```

**Reason**: The GitHub API token is missing from your settings.

---

## ✅ How to Fix It

### Step 1: Create GitHub Personal Access Token

1. Go to: **https://github.com/settings/tokens**

2. Click **"Generate new token (classic)"**
   ![Create Token Button](https://github.com/settings/tokens/new)

3. Fill in the form:
   ```
   Token name: Video Automation
   Expiration: 90 days (or No expiration if you prefer)
   ```

4. Select Scopes (check these boxes):
   ```
   ✓ repo                 (Full control of private repositories)
   ✓ workflow             (Update GitHub Action workflows)
   ```

5. Click **"Generate token"**

6. **COPY THE TOKEN** (you won't see it again!)
   ```
   The token looks like: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

---

### Step 2: Add Token to Your Settings

#### Option A: Via Dashboard (Easiest)
1. Open: **http://localhost/video-workflow-edit-enabled/settings.php**

2. Scroll down to **"GitHub Actions"** section

3. Find the field: **"GitHub API Token"**

4. Paste your token in the field

5. Make sure checkbox **"Enable GitHub Actions"** is checked ✓

6. Click **"Save Settings"**

#### Option B: Direct Database
```sql
UPDATE settings
SET setting_value = 'ghp_YOUR_TOKEN_HERE'
WHERE setting_key = 'github_api_token';

UPDATE settings
SET setting_value = '1'
WHERE setting_key = 'github_actions_enabled';
```

---

### Step 3: Verify Configuration

1. Go to: **http://localhost/video-workflow-edit-enabled/github-automation.php**

2. You should see:
   - ✅ GitHub Connection: **Connected**
   - Repo: **waqaskhan1437/my-video**
   - Branch: **main**

3. If still not working, check:
   - [ ] Token is pasted correctly (no extra spaces)
   - [ ] Token not expired
   - [ ] Token has `repo` and `workflow` scopes
   - [ ] `github_actions_enabled` is set to `1`

---

### Step 4: Add GitHub Secrets

For the workflow to work, you also need to add 2 secrets to your GitHub repo:

1. Go to: **https://github.com/waqaskhan1437/my-video**

2. Click: **Settings** → **Secrets and variables** → **Actions**

3. Click: **New repository secret**

Add these TWO secrets:

#### Secret #1
```
Name: AUTOMATION_API_KEY
Value: (your local API key)
```

#### Secret #2
```
Name: WORKFLOW_API_ENDPOINT
Value: http://localhost/video-workflow-edit-enabled
```
(or your actual domain if hosted on internet)

---

### Step 5: Test It!

1. Go to your dashboard

2. Edit an automation

3. Check: **"GitHub Actions Runner"**

4. Click: **Save**

5. Click: **"Run Automation"**

6. Should see: ✅ "Workflow dispatched to GitHub successfully!"

7. Check: **https://github.com/waqaskhan1437/my-video/actions** to see it running

---

## 🔑 Token Permissions Explained

- **repo**: Allows reading/writing to your repository files (needed to trigger workflows)
- **workflow**: Allows managing GitHub Actions workflows (needed to dispatch them)

---

## ⚠️ Important Security Notes

1. **Never share your token** - It's like a password
2. **Keep it private** - Don't commit it to any file
3. **Delete old tokens** - If you think it's compromised, delete it at https://github.com/settings/tokens
4. **Rotation** - Consider refreshing your token every 6-12 months

---

## 🐛 Troubleshooting

### "Failed to dispatch workflow to GitHub (HTTP 401)"
- Token is invalid or expired
- Token doesn't have `repo` scope
- Token has been deleted

### "Failed to dispatch workflow to GitHub (HTTP 404)"
- Repository name is wrong
- Branch name is wrong
- `.github/workflows/automation.yml` file doesn't exist in that branch

### "Failed to dispatch workflow to GitHub (HTTP 422)"
- Workflow file has syntax errors
- Input parameter format is wrong
- Owner/repo/branch combination doesn't exist

---

## 📝 Settings Summary

After setup, your settings should show:

| Setting | Value | Status |
|---------|-------|--------|
| github_actions_enabled | 1 | ✅ |
| github_api_token | ghp_xxx...xxx | ✅ (hidden) |
| github_repo_owner | waqaskhan1437 | ✅ |
| github_repo_name | my-video | ✅ |
| github_repo_branch | main | ✅ |

---

## 🎯 After Setup

Once token is added:
1. Edit any automation
2. Check "GitHub Actions Runner"
3. Save
4. Click "Run Automation"
5. Watch it execute on GitHub instead of your PC!

---

**Questions?** The error message will tell you exactly what's wrong when you try to run!
