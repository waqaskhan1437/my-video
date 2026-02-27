# GitHub Secrets Configuration Guide

**Location:** GitHub Repo > Settings > Secrets and variables > Actions

---

## 📋 Required Secrets

### 1. **AUTOMATION_API_KEY** (Required)
- **Purpose:** Authentication token for workflow API calls
- **Value:** Your API key (ask your admin)
- **Format:** `ghp_...` or your custom API key
- **Used By:** All workflows
- **Security:** Never share this in public repos

**Steps to add:**
1. Go to: `github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions`
2. Click: **New repository secret**
3. Name: `AUTOMATION_API_KEY`
4. Value: (paste your API key)
5. Click: **Add secret**

---

### 2. **WORKFLOW_API_ENDPOINT** (Required)
- **Purpose:** Base URL of your automation API
- **Value:** `https://your-domain.com` (without trailing slash)
- **Example:** `https://video-automation.example.com`
- **Used By:** All workflows (pipeline, social, postforme, whisper)
- **Important:** Must be HTTPS and accessible from GitHub

**Steps to add:**
1. Click: **New repository secret**
2. Name: `WORKFLOW_API_ENDPOINT`
3. Value: `https://your-domain.com`
4. Click: **Add secret**

---

## ✅ Verification Checklist

- [ ] `AUTOMATION_API_KEY` added
- [ ] `WORKFLOW_API_ENDPOINT` added
- [ ] Both secrets showing ✓ (not 🔴)

---

## 🔐 Security Best Practices

1. **Never commit secrets** - GitHub will auto-revoke exposed tokens
2. **Rotate API keys** - Change quarterly
3. **Use strong keys** - Generate via secure method
4. **Limit permissions** - API key should have minimum required access
5. **Monitor usage** - Check logs for unusual activity

---

## 🧪 Testing Your Secrets

After adding secrets, you can test them:

```bash
# In your repo, run a workflow and check logs:
1. Go to: Actions tab
2. Select: Any workflow
3. Click: Run workflow
4. Watch logs for errors about missing secrets
```

If you see `"Unauthorized: Invalid API key"` error, check:
- [ ] API key is correct
- [ ] Secret name matches exactly: `AUTOMATION_API_KEY`
- [ ] API endpoint is correct: `WORKFLOW_API_ENDPOINT`

---

## 📝 Workflow Secrets Usage

### In pipeline.yml
```yaml
curl -X POST "${{ secrets.WORKFLOW_API_ENDPOINT }}/api/..." \
  -H "Authorization: Bearer ${{ secrets.AUTOMATION_API_KEY }}"
```

### In social-publish.yml
```yaml
curl -X POST "${{ secrets.WORKFLOW_API_ENDPOINT }}/api/..." \
  -H "Authorization: Bearer ${{ secrets.AUTOMATION_API_KEY }}"
```

### In archive-postforme.yml
```yaml
curl -X POST "${{ secrets.WORKFLOW_API_ENDPOINT }}/api/..." \
  -H "Authorization: Bearer ${{ secrets.AUTOMATION_API_KEY }}"
```

### In whisper-cpu.yml
```yaml
curl -X POST "${{ secrets.WORKFLOW_API_ENDPOINT }}/api/..." \
  -H "Authorization: Bearer ${{ secrets.AUTOMATION_API_KEY }}"
```

---

## 🔑 How to Get Your API Key

### Option 1: GitHub Personal Access Token
1. Go to: https://github.com/settings/tokens
2. Click: **Generate new token (classic)**
3. Select scopes: `repo`, `workflow`
4. Copy token (won't show again!)

### Option 2: Fine-grained Token (Recommended)
1. Go to: https://github.com/settings/personal-access-tokens/new
2. Name: `VideoWorkflow`
3. Expiration: 90 days
4. Select your repository only
5. Grant: `Actions: Read & write`
6. Generate and copy

### Option 3: Custom API Key
- Ask your admin/developer for the automation API key

---

## 🚨 If Secret Leaks

**Immediately:**
1. Go to: Settings > Secrets and variables > Actions
2. Delete the compromised secret
3. Generate a new API key
4. Update the secret
5. Rotate all related credentials

---

## 📊 Example Configuration

```
Repository: my-video-automation
Branch: main

Secrets Added:
✓ AUTOMATION_API_KEY = ghp_abc123...xyz789
✓ WORKFLOW_API_ENDPOINT = https://video.example.com

Workflows Available:
✓ Google Photos to Archive
✓ Archive to YouTube
✓ Archive to PostForMe
✓ Whisper CPU Job
```

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| "Unauthorized" error | Check API key spelling, re-paste it |
| Secret not found | Verify secret name matches exactly |
| Endpoint unreachable | Check HTTPS URL, make sure server is online |
| 404 error | Verify endpoint path: `/api/github-automation-trigger.php` |

---

**Next Step:** After adding secrets, go to Actions tab and test a workflow!
