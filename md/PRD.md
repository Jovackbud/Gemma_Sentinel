# Gemma Sentinel — Product Requirements Document

**Version:** 1.0  
**Last Updated:** May 2026  
**Author:** [Your Name]  
**Status:** Active — Hackathon MVP  
**Competition:** DEV.to Gemma 4 Challenge (Build Track) · Deadline: May 24, 2026

---

## 1. Problem Statement

Fraud and scams are endemic across West Africa and the broader developing world. In Nigeria alone, citizens encounter advance-fee fraud ("419"), fake bank alerts, crypto scams, phishing WhatsApp messages, fake job offers, and romance scams daily. Existing detection tools either:

- Require an internet connection (privacy risk for sensitive financial screenshots)
- Are generic, Western-centric, and miss local scam patterns
- Operate only on text, ignoring the visual evidence (screenshots, fake receipts)
- Offer no reasoning — they classify without explaining _why_ something is a scam

Gemma Sentinel solves this by running a **multimodal, reasoning-first scam analysis pipeline entirely locally**, using Gemma 4's native vision and reasoning capabilities to analyse screenshots, text, and documents — and then explain its findings in plain language.

---

## 2. Product Vision

> "Point Gemma Sentinel at any suspicious message, screenshot, or document and get an honest, reasoned verdict in seconds — with no data leaving your device."

---

## 3. Goals

### Competition Goals (Primary)
- Win the DEV.to Gemma 4 Challenge "Build" category
- Demonstrate intentional, justified use of Gemma 4's multimodal + reasoning capabilities
- Produce a polished, demoable product with a memorable single-flow experience
- Justify model selection clearly and compellingly

### Product Goals (Secondary)
- Provide a genuinely useful tool for everyday users in fraud-heavy environments
- Show that local AI can power safety-critical applications without cloud dependency
- Establish a reference implementation for multimodal fraud detection with open models

---

## 4. Non-Goals (MVP Scope Exclusions)

- Mobile app (web app only for MVP)
- Voice note transcription and analysis (post-MVP)
- Fine-tuning Gemma 4 on scam data (out of scope)
- Real-time browser extension (post-MVP)
- User authentication or accounts
- Persistent storage of uploaded evidence

---

## 5. Target Users

| Persona | Description |
|---|---|
| **Everyday Nigerian/African citizen** | Receives suspicious WhatsApp messages, fake bank alerts, crypto offers |
| **Elderly or less tech-savvy user** | Needs plain-English explanation of why something is suspicious |
| **Journalist / researcher** | Needs to analyse a batch of scam evidence with reasoning trails |
| **Hackathon judge** | Needs to see Gemma 4 doing real, impressive multimodal reasoning work |

---

## 6. Core Features (MVP)

### 6.1 Evidence Ingestion
- Upload a screenshot (PNG, JPG, WEBP) — fake bank transfer, WhatsApp chat, email
- Paste raw text — SMS body, email content, chat transcript
- Upload a PDF — fake invoice, offer letter, contract

### 6.2 Multimodal Scam Analysis
- Gemma 4 reads the uploaded content (vision for images, text for typed/pasted content)
- Model reasons over the evidence using Gemma 4's thinking mode
- Identifies specific scam patterns: urgency language, impersonation, fake authority, request for payment

### 6.3 Verdict Output
- **Risk Score** — Low / Medium / High / Critical (with percentage confidence)
- **Scam Type** — Classification (phishing, 419, fake job, romance scam, crypto scam, fake bank alert, etc.)
- **Red Flags List** — Specific suspicious elements extracted from the evidence
- **Reasoning Explanation** — Plain-English paragraph explaining _why_ this is (or isn't) a scam
- **Recommended Action** — What the user should do next (ignore, report, block, verify independently)

### 6.4 Investigation Timeline (Differentiator Feature)
- When multiple pieces of evidence are uploaded in one session, Gemma correlates them
- Groups related scam patterns across inputs
- Generates a short "attack narrative" — how the scammer was building up to a request

### 6.5 Evidence Export
- Download a one-page PDF report of the analysis (for sharing with authorities or family)

---

## 7. Technical Requirements

### 7.1 Model

| Requirement | Choice | Justification |
|---|---|---|
| **Primary Model** | Gemma 4 27B MoE (via OpenRouter free tier) | Advanced reasoning + multimodal vision + efficient inference. MoE architecture means only ~4B parameters active per pass — fast enough for local-feel latency via API. |
| **Fallback Model** | Gemma 4 4B (via Gemini API free tier) | For users who want to run entirely locally with zero API cost |
| **Context Window** | 128K tokens | Allows feeding multiple pieces of evidence + full scam email bodies in one context |

**Why Gemma 4 specifically (competition narrative):**
> Gemma 4 is the only open model family that combines native multimodal understanding (seeing screenshots), advanced reasoning (thinking mode), and an efficient architecture that makes local/private deployment viable. No other open model at this scale can analyse a screenshot AND reason about why it's suspicious AND run without cloud dependency.

### 7.2 Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14 (App Router) + Tailwind CSS |
| **API layer** | Next.js API routes |
| **Model access** | OpenRouter API (Gemma 4 27B MoE) — free tier |
| **PDF export** | `react-pdf` or `jsPDF` |
| **File handling** | Browser FileReader API (no server-side storage) |
| **Deployment** | Vercel (free tier) |

### 7.3 Privacy Model
- All uploaded files are processed in-browser or via stateless API call
- **No files are stored server-side at any point**
- No user data is logged
- This is a hard requirement — fraud victims need to trust the tool

### 7.4 Performance Targets
- Time to first verdict: < 15 seconds for text input
- Time to first verdict: < 25 seconds for image input
- Works on any modern browser (Chrome, Firefox, Safari)

---

## 8. User Flow (The One Incredible Flow)

```
1. User lands on app → sees clear headline: "Is this a scam? Find out in seconds."
2. User uploads screenshot OR pastes text
3. User clicks "Analyse"
4. Loading state: "Gemma is reading the evidence..." (thinking mode indicator)
5. Results appear:
   ├── Risk Score badge (colour-coded)
   ├── Scam Type label
   ├── Red Flags (expandable list)
   ├── Reasoning paragraph (the wow moment)
   └── Recommended Action card
6. (Optional) User uploads second piece of evidence → Investigation Timeline appears
7. User downloads PDF report
```

---

## 9. Design Principles

- **Clarity over cleverness** — every output must be understandable by a non-technical user
- **Honest uncertainty** — if the model is unsure, say so explicitly (Low confidence score)
- **Locally relevant** — use Nigerian/West African scam examples in demo content
- **Privacy-first UI** — make it visually obvious that no data is being stored
- **Fast to wow** — the verdict should feel almost instantaneous

---

## 10. Success Metrics (Hackathon)

| Metric | Target |
|---|---|
| Judges can complete one full analysis flow | Yes, < 2 min |
| Model justification is explicit and compelling | Clear "why Gemma 4" statement in submission |
| Demo video is under 2 minutes and shows full flow | Yes |
| Code is clean, documented, and on GitHub | Yes |
| At least 3 scam types are demonstrable | 419 email, fake bank alert, fake job offer |

---

## 11. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| OpenRouter free tier rate limits during demo | Medium | Pre-record demo video; have fallback Gemini API key |
| Model hallucinates and says real message is a scam | Low–Medium | Add confidence threshold; show "uncertain" for borderline cases |
| Image input quality too low for Gemma vision | Low | Add image quality guidance in UI; test with actual screenshots |
| Too much scope, not enough polish | High | Ruthlessly cut to the single flow described in Section 8 |

---

## 12. Development Timeline

| Day | Milestone |
|---|---|
| Day 1 | Project scaffold (Next.js), OpenRouter API integration, text-only analysis working |
| Day 2 | Image upload + multimodal analysis working, basic results UI |
| Day 3 | Results page polish, Risk Score, Red Flags, Reasoning output |
| Day 4 | Investigation Timeline feature + PDF export |
| Day 5 | Testing with all 3 dataset sources, edge case handling |
| Day 6 | UI polish, mobile responsiveness, deploy to Vercel |
| Day 7 | Demo video recording, DEV.to submission write-up |

---

## 13. Submission Checklist

- [ ] GitHub repo public with clean README
- [ ] Live demo URL (Vercel)
- [ ] Demo video (≤ 2 min, shows full flow)
- [ ] DEV.to post using official submission template
- [ ] Model justification section clearly written
- [ ] At least 3 scam types tested and working
- [ ] PDF report export working
- [ ] No API keys committed to repo (use `.env.local`)
