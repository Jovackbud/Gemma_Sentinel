# Gemma Sentinel — Data Sources Guide

*Where to get every piece of test data you need, what it contains, and exactly how to use it.*

---

## Overview

You need three types of test data for Gemma Sentinel:

1. **Text-based scam samples** — SMS bodies, email content, chat transcripts
2. **Visual scam evidence** — screenshots of fake bank alerts, phishing websites, fake receipts
3. **Document scam samples** — fake invoices, offer letters, fraudulent PDFs

All sources below are free, openly licensed, and require no payment or credit card.

---

## Source 1: Mendeley SMS Phishing Dataset

**URL:** https://data.mendeley.com/datasets/f45bkkt8pr/1  
**Format:** CSV + Python scripts  
**Size:** 5,971 labelled messages  
**License:** CC BY 4.0  
**Access:** Free download, no account required

### What's In It

Three categories of messages:
- `ham` — 4,844 legitimate messages
- `spam` — 489 spam messages
- `smishing` — 638 SMS phishing messages

The smishing category is your goldmine. These are real SMS phishing messages used in actual attacks, labelled and cleaned. The dataset also includes extracted attributes per message: URLs found, phone numbers, email addresses — all useful for building your analysis context.

### How to Use It

```python
import pandas as pd

df = pd.read_csv('smishing_dataset.csv')
scam_messages = df[df['LABEL'] == 'Smishing']['TEXT'].tolist()

# Pick 10–15 varied examples for your demo test suite
demo_samples = scam_messages.sample(15, random_state=42)
```

**Best samples to cherry-pick for demo:**
- Messages containing "verify your account" + a fake URL
- Messages impersonating a bank with "your account has been suspended"
- Messages promising a prize with an activation fee

---

## Source 2: difraud — Domain-Independent Fraud Detection Benchmark

**URL:** https://huggingface.co/datasets/difraud/difraud  
**Also at:** https://huggingface.co/datasets/redasers/difraud  
**Format:** HuggingFace Dataset (JSON/Parquet)  
**Size:** 95,854 samples across 7 domains  
**License:** Research use — cite as: ReDAS Lab, University of Houston, 2023  
**Access:** Free, HuggingFace account optional

### What's In It

Seven fraud domains, all labelled as deceptive or non-deceptive:

| Domain | Samples | Useful For |
|---|---|---|
| Phishing emails | ~152 | Email phishing demos |
| Job scam listings | 17,880 | Fake recruitment demos |
| Fake reviews | Large | Pattern comparison |
| Fake news | 72,134 | Misinformation angle |
| Romance fraud | Included | WhatsApp romance scam demos |
| Spam | Included | SMS scam baseline |
| Deceptive opinions | Included | Social engineering patterns |

### How to Use It

```python
from datasets import load_dataset

dataset = load_dataset("difraud/difraud")

# Get job scam examples
job_scams = dataset['train'].filter(lambda x: x['task'] == 'job_scam' and x['label'] == 1)

# Get phishing email examples
phishing = dataset['train'].filter(lambda x: x['task'] == 'phishing' and x['label'] == 1)
```

**Best samples to use for demo:**
- From job_scam: entries mentioning upfront fees, unverifiable company names, urgency
- From phishing: short email bodies with bank impersonation

---

## Source 3: 419scam.org Archive

**URL:** http://www.419scam.org/emails/  
**Format:** Plain text, web-browsable  
**Size:** Thousands of real scam emails, organised by category  
**License:** Public domain (submitted by scam victims)  
**Access:** Free, no account

### What's In It

Real advance-fee fraud emails, submitted by recipients. Categories include:

- Business proposals / investment fraud
- Lottery and prize fraud
- Inheritance and estate fraud
- Diplomatic/fund transfer fraud
- Romance fraud
- Black money / washwash fraud

This is the most Nigeria-specific dataset available. The emails contain the exact language, names, and patterns used by real 419 scammers.

### How to Use It

Browse the site manually and save 5–10 representative email bodies as `.txt` files into your `/public/demo/` folder. Look for:

- Emails with formal/official-sounding language from fake "government" entities
- Emails with emotional hooks (widow, inheritance, orphan)
- Emails that escalate — first contact, then follow-up asking for fees

**Important:** Strip any real email addresses or phone numbers from saved samples before including them in your public repo.

---

## Source 4: CIRCL Phishing Website Screenshots

**URL:** https://www.circl.lu/opendata/datasets/circl-phishing-dataset-01  
**Format:** Image files (PNG/JPEG)  
**Size:** 400+ human-verified screenshots  
**License:** Open research license  
**Access:** Free download

### What's In It

Screenshots of real phishing websites, human-verified and human-classified. Includes:
- Fake bank login pages
- Fake payment portals
- Spoofed corporate websites
- Fake prize/lottery landing pages

All screenshots have been reviewed and any personally identifiable content removed.

### How to Use It

Download the dataset and select 3–5 clear, visually convincing screenshots for your demo. Ideal candidates:
- Screenshots where the visual deception is obvious once pointed out (wrong logo, URL mismatch visible in screenshot)
- Screenshots that look professionally made — the more convincing, the more impressive Gemma's detection will seem

These screenshots are your multimodal demo assets. They are what allows you to say "Gemma is reading the image, not just text."

---

## Source 5: Your Own Curated Screenshots (Highest Impact)

**Source:** Your own device, family, colleagues in Nigeria  
**Format:** PNG or JPEG  
**Access:** Free — you already have them

### Why This Is Your Best Asset

Nothing will make your demo more authentic and locally resonant than real examples from your own context. Every Nigerian has received scam messages. The patterns you recognise intuitively — the slightly off GTBank logo, the Access Bank alert that uses a different green, the "customer service" WhatsApp number with a foreign country code — are exactly the patterns that make a West African-specific demo feel genuine.

### What to Collect

| Type | How to Get It |
|---|---|
| Fake bank transfer alert | Check your personal WhatsApp for received messages; ask family |
| Fake PalmPay/OPay/Kuda alert | Common in Nigeria — check groups |
| Fake job offer | LinkedIn InMail, WhatsApp groups, Telegram channels |
| Crypto "doubling" scheme | Twitter/X DMs, WhatsApp broadcast lists |
| Fake EFCC/FIRS notice | Common email phishing in Nigeria |

### Privacy Guidelines

Before using any screenshot:
- Remove real phone numbers of senders
- Remove your own name if visible
- Remove any real account numbers
- If a third party is visible (a family member who forwarded it), get their consent or blur identifying info

For the public repo `/public/demo/` folder, only include samples you've either created yourself (mockups) or that you have cleared of personal information. More sensitive real examples can be tested locally but kept out of the public repo.

---

## Source 6: Kaggle Bank Account Fraud Dataset (NeurIPS 2022)

**URL:** https://www.kaggle.com/datasets/sgpjesus/bank-account-fraud-dataset-neurips-2022  
**Format:** CSV  
**Size:** Large structured dataset  
**License:** Open (requires free Kaggle account)  
**Access:** Free with Kaggle login

### What's In It

Realistic synthetic bank account fraud transaction data from NeurIPS 2022. Tabular data with transaction features — amounts, timestamps, merchant categories, etc.

### How to Use It

This is useful for a secondary demo: paste a series of suspicious transaction logs into Gemma Sentinel as text and ask it to reason about financial patterns. Shows the 128K context window being used for long structured data, not just short messages.

```text
# Sample prompt structure:
"Here are 50 recent transactions from a user's account. 
Analyse them for suspicious patterns consistent with fraud."

[Paste 50 rows of CSV data as plain text]
```

---

## Source 7: arXiv Papers (for ContextCraft cross-reference)

*Only needed if you add the "compare documents" feature to Sentinel.*

**URL:** https://huggingface.co/datasets/armanc/scientific_papers  
**Format:** JSON with full paper text  
**Access:** Free, no account

Use this to demonstrate that Gemma Sentinel can also analyse long documents (e.g., a suspicious investment prospectus or a fake "government" report). Feed multiple pages into a single Gemma call and show the 128K context window working.

---

## Recommended Demo Test Suite

Save these into `/public/demo/` in your repo:

```
public/
└── demo/
    ├── text/
    │   ├── 419-advance-fee-email.txt       # From 419scam.org
    │   ├── fake-job-offer-whatsapp.txt     # From difraud job_scam subset
    │   ├── bank-account-suspended-sms.txt  # From Mendeley smishing dataset
    │   └── crypto-investment-offer.txt     # Write your own or from difraud
    ├── images/
    │   ├── fake-bank-alert-mockup.png      # Your own mockup
    │   ├── phishing-site-screenshot.png    # From CIRCL dataset
    │   └── crypto-scam-social-post.png     # Your own screenshot
    └── documents/
        └── fake-invoice-sample.pdf         # Create in Canva/Google Docs
```

---

## Quick Setup Script

Run this once to download and organise your text datasets:

```bash
#!/bin/bash
# setup_demo_data.sh

# Install HuggingFace CLI
pip install huggingface_hub datasets

# Create demo directories
mkdir -p public/demo/text public/demo/images public/demo/documents

# Download difraud dataset samples
python3 - <<EOF
from datasets import load_dataset
import json

ds = load_dataset("difraud/difraud", split="train")

# Save 10 job scam examples
job_scams = [x for x in ds if x.get('task') == 'job_scam' and x.get('label') == 1][:10]
with open('public/demo/text/job-scams-sample.jsonl', 'w') as f:
    for item in job_scams:
        f.write(json.dumps({'text': item['text'], 'label': 'fraud'}) + '\n')

print(f"Saved {len(job_scams)} job scam samples")
EOF

echo "Demo data setup complete. Check public/demo/"
```

---

## Citation / Attribution

If your DEV.to submission mentions the datasets (recommended for credibility), use these attributions:

> **SMS Phishing Dataset:** Mishra, S., & Soni, D. (2020). Smishing Detector: A security model to detect smishing through SMS content analysis and URL behavior analysis. Future Generation Computer Systems. https://doi.org/10.1016/j.future.2020.03.021

> **difraud Benchmark:** ReDAS Lab, University of Houston (2023). Domain Independent Fraud Detection Benchmark. https://huggingface.co/datasets/difraud/difraud

> **CIRCL Phishing Screenshots:** CIRCL (Computer Incident Response Center Luxembourg). Open Dataset of Phishing Website Screen-captures. https://www.circl.lu/opendata/datasets/circl-phishing-dataset-01
