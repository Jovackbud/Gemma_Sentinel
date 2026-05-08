# Gemma Sentinel — Demo Guide

*Everything you need to record a winning demo video and present the project live.*

---

## Demo Philosophy

The judges for the DEV.to Gemma 4 Challenge will evaluate hundreds of submissions. Your demo video is the single most important asset — it is what they will watch first, and for most entries, the only thing they will engage with deeply.

The goal is one thing: **make Gemma 4 look genuinely impressive doing real work.**

Not a chatbot. Not a wrapper. A tool that looks at a scam screenshot, reasons through it intelligently, and explains itself clearly. That experience, done well, is the win.

**Guiding rule:** Every second of the demo should show Gemma 4 doing something a simple `if/else` rule couldn't do.

---

## Demo Format

**Target length:** 90 seconds (hard cap at 2 minutes)  
**Format:** Screen recording with voiceover  
**Tools:** OBS Studio (free), Loom (free), or macOS/Windows built-in screen recorder  
**Resolution:** 1080p minimum  
**Voiceover:** Your own voice — authenticity matters

---

## The Three-Scenario Demo Structure

Structure your demo around three fast, distinct scenarios. Each one takes about 25 seconds. Together they show the full range of Gemma 4's capabilities.

---

### Scenario 1 — The Fake Bank Alert (Screenshot, 25 seconds)

**What you're demonstrating:** Gemma 4's native vision capability. It reads a screenshot — not OCR'd text, the actual image — and reasons about visual inconsistencies.

**The asset:** A screenshot of a fake bank transfer alert (GTBank or Access Bank style). Use a real example from the CIRCL dataset or create a clean mockup. Key elements to include:
- Slightly wrong bank logo (colour off, font different)
- Amount that seems large and tempting (e.g., ₦750,000)
- A message saying "send ₦7,500 to activate the transfer"

**What to say:**
> "I'll start with the most common scam in Nigeria — the fake bank transfer alert. Watch what Gemma sees."

*[Upload screenshot. Click Analyse. Wait for result.]*

> "Gemma didn't just read the text. It noticed the logo inconsistency, the font mismatch in the amount field, and the classic advance-fee pattern — pay to receive. That visual reasoning is only possible with Gemma 4's native multimodal capability."

**Expected output to show:**
- Risk Level: Critical
- Scam Type: Advance Fee / Fake Bank Alert
- Red Flags: Logo inconsistency, advance fee pattern, urgency language
- Reasoning: 2–3 sentence explanation

---

### Scenario 2 — The WhatsApp Job Offer (Text, 20 seconds)

**What you're demonstrating:** Text-based reasoning. Gemma 4 recognises the psychological tactics — urgency, vague authority, payment request — even in a short message.

**The asset:** A pasted WhatsApp message. Example:

> "Good afternoon. I am Mr. Emmanuel Okafor, HR Director at Chevron Nigeria Ltd. We have reviewed your profile and you have been shortlisted for a Logistics Coordinator position. Salary: ₦450,000/month. To proceed, please pay a ₦15,000 registration fee to secure your slot before Friday. Reply ASAP as we have many candidates."

**What to say:**
> "Now just a pasted WhatsApp message. No image — pure text reasoning."

*[Paste text. Click Analyse.]*

> "It caught the fake authority, the artificial deadline, the payment request, and the vague credentials — all in under 10 seconds."

**Expected output to show:**
- Risk Level: High
- Scam Type: Fake Job Offer / Advance Fee
- Red Flags: Unsolicited contact, payment required before employment, urgency pressure, unverifiable identity

---

### Scenario 3 — The Investigation Timeline (Multi-evidence, 25 seconds)

**What you're demonstrating:** The differentiator feature. Gemma 4 connects multiple pieces of evidence and builds a coherent attack narrative. This is what no simple scam checker does.

**What to say:**
> "The real power comes when you have multiple pieces. Imagine this is a case — you've received all of these over a week."

*[Upload the bank alert screenshot AND paste the job offer message together in one session. Click Analyse.]*

> "Gemma is now reasoning across both pieces of evidence. Watch."

*[Show the Investigation Timeline panel]*

> "It recognised that these two messages are likely from the same criminal operation — both use advance-fee tactics, both create artificial urgency, and it's flagged the escalation pattern: start with a fake job, follow up with a fake payment confirmation to add credibility. That's Gemma 4's 128K context window and reasoning mode working together."

**Expected output to show:**
- Combined risk assessment
- Attack narrative: "This appears to be a two-stage fraud operation..."
- Timeline connecting the two events

---

### Closing (5 seconds)

> "Gemma Sentinel — multimodal fraud detection, powered entirely by Gemma 4, running locally with no data stored. Built for the people who need it most."

*[Show the "Download Report" button being clicked]*

---

## Technical Demo Setup

### Before You Record

1. **Test all three scenarios at least 5 times** — know exactly what Gemma 4 will output for each input
2. **Prepare your `.env.local`** with a working OpenRouter key — don't do a live API setup during recording
3. **Clear your browser** — no other tabs open, clean browser history, no notifications
4. **Set screen resolution** to 1920×1080 or 2560×1440
5. **Zoom your browser to 125%** — text should be clearly readable in the recording
6. **Disable notifications** on all devices in the room

### The "Loading" Moment

The 15–25 second wait while Gemma thinks is actually a feature, not a bug. Use it.

During the loading state, show a subtle "Gemma is reasoning..." indicator in the UI. In your voiceover, say something like:

> "You can see Gemma is actually thinking through this — not just pattern-matching keywords."

This turns a loading spinner into a demonstration of Gemma 4's reasoning mode.

### If the API Is Slow

Have a pre-recorded fallback of the results page that you can cut to. Judges understand APIs have latency — they don't need to watch a spinner for 45 seconds. Record the analysis portion separately if needed and cut to it.

---

## Demo Assets to Prepare

Create these files and save them in `/public/demo/` in the repo:

| File | How to Get It |
|---|---|
| `fake-bank-alert.png` | Create a mockup in Canva or Figma using a real bank's public logo style. Make it look convincing but clearly fake (wrong colours, off-brand font). |
| `whatsapp-job-scam.txt` | Write your own based on real patterns. Keep it under 150 words. |
| `419-email-sample.txt` | Download from the difraud HuggingFace dataset (see DATA_SOURCES.md) |
| `crypto-scam.png` | Screenshot a "crypto doubling" social media ad or create a mockup |
| `fake-invoice.pdf` | Create a simple PDF with a made-up company name, logo, and payment request |

**Important:** Do not use screenshots of real people's real scam messages without their permission. Use dataset samples or your own mockups for the public demo.

---

## What to Highlight in the DEV.to Write-Up

The written submission post is evaluated equally with the demo. Make sure you explicitly address each judging criterion.

### Judging Criterion 1: Intentional Model Choice
Write a dedicated section. Sample text:

> "I chose Gemma 4 27B MoE for three specific reasons that no other model could satisfy simultaneously: (1) native multimodal vision to read screenshots without a separate OCR pipeline, (2) thinking/reasoning mode to explain *why* something is a scam rather than just classifying it, and (3) the efficient MoE architecture that keeps inference fast enough for a real user experience while leaving open the path to fully local deployment via the 4B variant. A model without native vision would miss the forged logos. A model without reasoning mode would give verdicts users can't trust or verify. No other open model at this scale combines all three."

### Judging Criterion 2: Technical Implementation
Link directly to these files in your repo:
- `lib/gemma.ts` — shows how you're calling the model
- `lib/prompts.ts` — shows your prompting strategy
- `app/api/analyse/route.ts` — shows the analysis pipeline

### Judging Criterion 3: Creativity and Originality
Emphasise:
- The locally-relevant angle (Nigerian/West African scam patterns)
- The Investigation Timeline feature (multi-evidence correlation)
- The privacy-first architecture (no server-side storage)

### Judging Criterion 4: Usability
Show the one clean flow. Mention that a non-technical user can upload a screenshot and read the verdict without understanding anything about AI.

---

## Live Demo Checklist (If Presenting Live)

- [ ] OpenRouter API key is active and has remaining free credits
- [ ] All three demo scenarios tested within the last hour
- [ ] Vercel deployment is live and responding
- [ ] Backup: local dev server running as fallback
- [ ] Browser zoom set to 125%
- [ ] Demo assets in `/public/demo/` are accessible
- [ ] PDF export button works
- [ ] Tested on the presentation machine/browser specifically

---

## Anticipated Judge Questions and Answers

**"Why not use GPT-4o for this?"**
> "GPT-4o is excellent but it's a closed, cloud-only model. Fraud victims cannot upload screenshots of their bank accounts to a third-party cloud API — that's a major privacy and security issue. Gemma 4 uniquely allows the identical capability to run entirely on-device. The 4B variant runs on a laptop with no API calls at all. That's the only way this tool can be responsibly deployed in the communities that need it most."

**"How accurate is it?"**
> "For the demo scenarios I've tested, Gemma 4 correctly identifies all known scam types with appropriate reasoning. I'm not claiming 99% accuracy as a production fraud system — this is a reasoning assistant, not a binary classifier. What matters is that it explains its reasoning so the user can make an informed decision, rather than just saying 'scam' like a spam filter."

**"What makes this different from a simple keyword filter?"**
> "A keyword filter would have been triggered by 'send money' and that's it. Gemma Sentinel looks at a PNG image, identifies that a bank logo has the wrong shade of red, notices the font inconsistency in the amount field, connects that to the advance-fee pattern in the text, and explains all of that in plain English. None of that is possible with keywords."

**"Could this be misused to help scammers make better scams?"**
> "The output is framed entirely around user protection — red flags and recommended actions. Nothing in the output teaches scam technique. The same risk applies to any security education tool; the benefits to the far larger population of potential victims vastly outweigh the marginal risk."
