# CineVibe Security Audit Report

**Date:** November 4, 2025
**Auditor:** Claude Code
**Scope:** Full codebase security audit for exposed secrets and credentials

---

## Executive Summary

This security audit identified **3 CRITICAL** exposed secrets, **2 MEDIUM** severity issues, and several **LOW** severity configuration exposures in the CineVibe codebase.

**IMMEDIATE ACTION REQUIRED:**
- Rotate Google Maps API key: `AIzaSyAbT-yRBrPeWjyeIpPw7hgQ41iB-YsGo_s`
- Invalidate Claude AI OAuth tokens
- Remove sensitive files from repository and git history

---

## Critical Findings

### 1. Google Cloud Maps API Key - EXPOSED ⚠️ CRITICAL

**Location:** `/home/user/CineVibe/mapkey.txt`
**Type:** Google Cloud Maps API Key
**Value:** `AIzaSyAbT-yRBrPeWjyeIpPw7hgQ41iB-YsGo_s`

**Risk:**
- Unauthorized use of Google Maps API
- Potential billing charges on your GCP account
- Service abuse or quota exhaustion
- API key can be used from any IP/domain without restrictions

**Remediation:**
1. Immediately revoke this API key in Google Cloud Console
2. Create a new API key with restrictions (HTTP referrer, IP address, API restrictions)
3. Store new key in environment variable `GOOGLE_MAPS_API_KEY`
4. Delete `mapkey.txt` from repository
5. Purge from git history using `git filter-branch` or BFG Repo-Cleaner

---

### 2. Claude AI OAuth Tokens - EXPOSED ⚠️ CRITICAL

**Location:** `/home/user/CineVibe/.claude/.credentials.json`
**Type:** OAuth Access & Refresh Tokens

**Exposed Credentials:**
- **Access Token:** `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`
- **Refresh Token:** `sk-ant-ort01-e5dNNf1WAwBk4erGST3-1k3FfaO-qjXEQNLBcJpVhO7nT2B7zowiet9P3pxJDXmz9S_4rrmB-Qj76WR6Hh6OKA-wD8LmqQAA`
- **Expiration:** November 4, 2025, 12:00:36 GMT (still valid)
- **Scopes:** `user:inference`, `user:profile`

**Risk:**
- Unauthorized access to Claude AI API
- Potential API abuse and billing charges
- Profile information exposure
- Token has not yet expired and is actively usable

**Remediation:**
1. Revoke these OAuth tokens immediately via Claude AI console
2. Re-authenticate and generate new tokens
3. Add `.claude/` directory to `.gitignore`
4. Never commit credential files
5. Purge from git history

---

### 3. Hardcoded Flask Secret Key - MEDIUM SEVERITY ⚠️

**Location:** `/home/user/CineVibe/cinevibe-bootstrap/cinevibe/app.py:28`

```python
app.secret_key = os.environ.get("SECRET_KEY", "cinevibe-secret-key-change-in-production")
```

**Risk:**
- Weak default fallback secret key
- If `SECRET_KEY` environment variable is not set, application uses hardcoded default
- Compromises session security and cookie signing
- Default value explicitly warns "change-in-production" but remains in code

**Remediation:**
1. Remove hardcoded fallback value
2. Require `SECRET_KEY` to be set via environment variable
3. Generate strong random secret: `python -c 'import secrets; print(secrets.token_hex(32))'`
4. Update code to fail fast if SECRET_KEY not provided:

```python
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY environment variable must be set")
```

---

### 4. API Key in Bash History - MEDIUM SEVERITY ⚠️

**Location:** `/home/user/CineVibe/.bash_history`
**Lines:** 48, 58, 82-84, 95-96, 108, 112

**Exposed Commands:**
```bash
export KEY_DISPLAY_NAME="AIzaSyAbT-yRBrPeWjyeIpPw7hgQ41iB-YsGo_s"
export GOOGLE_MAPS_KEY_ID="AIzaSyAbT-yRBrPeWjyeIpPw7hgQ41iB-YsGo_s"
echo "${GOOGLE_MAPS_API_KEY}" > ~/mapkey.txt
```

**Risk:**
- Bash history persists and can be reviewed by anyone with shell access
- API key exposed in multiple command variations
- Creates audit trail of sensitive operations

**Remediation:**
1. Clear bash history: `history -c && history -w`
2. Add `.bash_history` to `.gitignore`
3. Use `HISTCONTROL=ignorespace` and prefix sensitive commands with space
4. Consider disabling history for sensitive sessions

---

### 5. Google Cloud Project ID - LOW SEVERITY ℹ️

**Location:** `/home/user/CineVibe/project_id.txt`
**Value:** `gen-lang-client-0871164439`

**Risk:**
- Project IDs are not sensitive alone (often visible in URLs)
- Combined with API keys, can be used for targeted attacks
- May reveal infrastructure details

**Remediation:**
1. Remove from repository (use environment variable instead)
2. Reference via `GOOGLE_CLOUD_PROJECT` environment variable
3. Add `project_id.txt` to `.gitignore`

---

## Good Security Practices Found ✅

The audit also identified several **positive security practices** already in place:

1. **Environment Variable Usage:**
   - API keys for Runway, Pika, Midjourney, Stability AI properly use `os.environ.get()`
   - Database credentials retrieved from environment variables
   - No hardcoded database passwords found

2. **Configuration Management:**
   - Cloud Build YAML files use variable substitution
   - Deployment scripts leverage environment variables

3. **No Committed .env Files:**
   - No actual `.env` files with secrets are committed to repository

---

## Files Requiring Action

### Files to Delete from Repository:
1. `/home/user/CineVibe/mapkey.txt` - Contains Google Maps API key
2. `/home/user/CineVibe/.claude/.credentials.json` - Contains OAuth tokens
3. `/home/user/CineVibe/.bash_history` - Contains API key references
4. `/home/user/CineVibe/project_id.txt` - Contains GCP project ID

### Files to Update:
1. `/home/user/CineVibe/cinevibe-bootstrap/cinevibe/app.py` - Remove hardcoded Flask secret fallback
2. `/home/user/CineVibe/.gitignore` - Add exclusions for sensitive files

---

## Recommended .env Structure

Create a `.env.example` file (safe to commit) with this structure:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here-generate-with-secrets-token-hex

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# AI Service API Keys (if needed in future)
RUNWAY_API_KEY=
PIKA_API_KEY=
MIDJOURNEY_API_KEY=
STABILITY_AI_API_KEY=

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/cinevibe

# Claude AI (keep in separate secure location, not .env)
# CLAUDE_ACCESS_TOKEN=
# CLAUDE_REFRESH_TOKEN=
```

**Actual `.env` file** (never commit):
```bash
SECRET_KEY=<generate-random-64-char-hex>
GOOGLE_CLOUD_PROJECT=gen-lang-client-0871164439
GOOGLE_MAPS_API_KEY=<new-rotated-key-with-restrictions>
```

---

## Recommended .gitignore Updates

Add these entries to `.gitignore`:

```gitignore
# Environment files
.env
.env.local
.env.*.local
.env.production

# Secret files
*.key
*.pem
*.p12
credentials.json
*credentials*.json
mapkey.txt
project_id.txt

# Shell history
.bash_history
.zsh_history

# Claude AI
.claude/
.claude.json

# Gemini
.gemini/

# Python virtual environments
env/
venv/
ENV/
```

---

## Immediate Action Checklist

- [ ] **CRITICAL:** Revoke Google Maps API key in Google Cloud Console
- [ ] **CRITICAL:** Invalidate Claude AI OAuth tokens
- [ ] **CRITICAL:** Generate new API keys with proper restrictions
- [ ] Delete `mapkey.txt` from repository
- [ ] Delete `.claude/.credentials.json` from repository
- [ ] Delete `project_id.txt` from repository
- [ ] Remove `.bash_history` from repository
- [ ] Update `.gitignore` with recommended exclusions
- [ ] Create `.env.example` file
- [ ] Update `app.py` to require SECRET_KEY environment variable
- [ ] Purge sensitive data from git history using BFG Repo-Cleaner
- [ ] Set up pre-commit hooks for secret scanning
- [ ] Document secret management process for team
- [ ] Implement Google Secret Manager for production secrets

---

## Tools for Ongoing Security

Consider implementing these tools:

1. **git-secrets** - Prevents committing secrets to git
   ```bash
   git secrets --install
   git secrets --register-aws
   ```

2. **truffleHog** - Scans git history for secrets
   ```bash
   trufflehog git file://. --only-verified
   ```

3. **detect-secrets** - Pre-commit hook for secret detection
   ```bash
   pip install detect-secrets
   detect-secrets scan
   ```

4. **GitHub Secret Scanning** - Enable in repository settings

---

## Contact Information

For questions about this audit or remediation assistance, refer to:
- CineVibe security documentation
- Google Cloud Security Best Practices
- OWASP Secret Management Cheat Sheet

---

**Report Generated:** November 4, 2025
**Status:** Requires Immediate Action
