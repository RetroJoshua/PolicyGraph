# How to Get Scraped Policies Data

The scraped policies (959 files, ~4 MB) are not committed to Git because
they are too large and can be regenerated. Here's how to get them.

---

## Option 1: Download the Pre-Scraped Archive (Fastest — No Token Needed)

A pre-built archive of 959 scraped IAM policies is available.

### Download

The archive files are located in the project root (on the VM):
- `scraped_policies.tar.gz` (124 KB)
- `scraped_policies.zip` (436 KB)

### Extract on Windows

**Using the `.zip` file (easiest on Windows):**
```cmd
cd C:\Users\user\Documents\CMRIT\projects\PolicyGraph

:: Right-click scraped_policies.zip → "Extract All..."
:: OR use PowerShell:
Expand-Archive -Path scraped_policies.zip -DestinationPath .
```

**Using the `.tar.gz` file (Git Bash):**
```bash
cd ~/Documents/CMRIT/projects/PolicyGraph
tar -xzf scraped_policies.tar.gz
```

### Verify

```bash
ls data/scraped_policies/ | wc -l
# Should show: 960 (959 .tf files + 1 manual_labels.csv)
```

---

## Option 2: Use the 10-Policy Sample (For Quick Testing)

A small sample of 10 representative policies is included in the repo at
`data/scraped_policies_sample/`. This is enough to test the labeling
workflow without needing the full dataset.

```bash
# Test the labeling tool with the sample
python scripts/label_scraped_policies.py \
    --scraped data/scraped_policies_sample \
    --out data/labeled_policies \
    --model checkpoints/long/best_model.pt \
    --score-only

# Should score 10 policies successfully
```

The sample includes a mix of:
- `aws_iam_policy_document` (4 files)
- `aws_iam_policy` (2 files)
- `aws_iam_role` (2 files)
- `aws_iam_role_policy` (2 files)

With patterns: PassRole, iam:*, wildcard actions, and normal/secure policies.

---

## Option 3: Re-Scrape with a GitHub Token

If you want fresh data or more policies, create a GitHub token and re-scrape.

### Step 1: Create a GitHub Personal Access Token

1. Go to: **https://github.com/settings/tokens**
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Settings:
   - **Note:** `PolicyGraph Scraper`
   - **Expiration:** 30 days
   - **Scopes:** Check **ONLY** `public_repo` (nothing else needed)
4. Click **"Generate token"**
5. **COPY THE TOKEN** immediately (you won't see it again!)

> The token looks like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 2: Set Token and Run Scraper

**On Git Bash (Windows):**
```bash
# Set the token (replace with your actual token)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# Verify it's set
echo $GITHUB_TOKEN

# Navigate to project
cd ~/Documents/CMRIT/projects/PolicyGraph

# Activate virtual environment
source .venv/Scripts/activate

# Install scraper dependencies (if not already)
pip install requests python-hcl2 tqdm

# Run scraper (3 pages ≈ 959 policies, takes ~15-20 minutes)
python scripts/scrape_iam_terraform.py --pages 3 --out data/scraped_policies
```

**On Windows CMD:**
```cmd
:: Set the token
set GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

:: Navigate to project
cd C:\Users\user\Documents\CMRIT\projects\PolicyGraph

:: Activate virtual environment
.venv\Scripts\activate

:: Install dependencies
pip install requests python-hcl2 tqdm

:: Run scraper
python scripts\scrape_iam_terraform.py --pages 3 --out data\scraped_policies
```

**On Windows PowerShell:**
```powershell
# Set the token
$env:GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"

# Navigate and run
cd ~\Documents\CMRIT\projects\PolicyGraph
.venv\Scripts\Activate.ps1
pip install requests python-hcl2 tqdm
python scripts/scrape_iam_terraform.py --pages 3 --out data/scraped_policies
```

### Expected Output

```
INFO Query: aws_iam_policy_document extension:tf
INFO   Page 1/3
INFO   Page 2/3
INFO   Page 3/3
INFO Saved so far: 183
INFO Query: aws_iam_role_policy extension:tf
...
INFO Done. Total unique policies/blocks saved: 959
```

### Rate Limits

| Authentication | Search Rate | Hourly Limit |
|---------------|-------------|-------------|
| **With token** | 30 req/min | 5,000 req/hr |
| **Without token** | 10 req/min | 60 req/hr |

The scraper handles rate limits automatically (backs off on 403 errors).

### Want More Policies?

```bash
# 5 pages ≈ ~1,500 policies
python scripts/scrape_iam_terraform.py --pages 5 --out data/scraped_policies

# 10 pages ≈ ~3,000 policies
python scripts/scrape_iam_terraform.py --pages 10 --out data/scraped_policies
```

---

## Verification (After Any Option)

```bash
# Count files
ls data/scraped_policies/ | wc -l
# Expected: ~960

# Check file types
ls data/scraped_policies/raw_*.tf | wc -l
# Expected: ~959

# Quick content check
head -20 data/scraped_policies/raw_*.tf | head -40

# Test the labeling tool
python scripts/label_scraped_policies.py \
    --scraped data/scraped_policies \
    --out data/labeled_policies \
    --model checkpoints/long/best_model.pt \
    --score-only --limit 5
# Should show: 5 scored, distribution of vulnerable/secure
```

---

## Troubleshooting

### "401 Unauthorized" when scraping

**Cause:** No GitHub token set, or token expired.

**Fix:** Create a new token (see Option 3, Step 1) and set it:
```bash
export GITHUB_TOKEN="ghp_your_new_token_here"
```

### "403 Rate Limited" when scraping

**Cause:** Too many requests without a token.

**Fix:**
1. Get a GitHub token (see Option 3)
2. The scraper auto-handles rate limits, but with a token you get 5× more requests

### "No module named 'requests'" or "No module named 'hcl2'"

**Fix:**
```bash
pip install requests python-hcl2 tqdm
```

### Archive extraction fails on Windows

**Fix:** Use 7-Zip (free): https://www.7-zip.org/
- Right-click → 7-Zip → Extract Here

Or use PowerShell:
```powershell
Expand-Archive -Path scraped_policies.zip -DestinationPath .
```
