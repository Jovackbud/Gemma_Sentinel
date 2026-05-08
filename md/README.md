# 🛡️ Gemma Sentinel

**Offline-first AI scam and fraud detector powered by Gemma 4.**

Upload a suspicious screenshot, paste a message, or drop in a document — Gemma Sentinel tells you whether it's a scam, what type it is, exactly why it's suspicious, and what you should do next. All analysis runs through Gemma 4's native multimodal reasoning. No data is stored.

> Built for the [DEV.to Gemma 4 Challenge](https://dev.to/challenges/gemma) · May 2026

---

## ✨ What It Does

- **Analyses screenshots** — fake bank transfers, WhatsApp chats, phishing emails, fake receipts
- **Reads pasted text** — SMS bodies, email content, chat transcripts
- **Understands PDFs** — fake offer letters, fraudulent invoices, scam contracts
- **Gives you a verdict** — Risk score, scam type, specific red flags, plain-English reasoning
- **Builds an investigation timeline** — when you upload multiple related pieces, Gemma connects the dots and tells the full attack story
- **Exports a report** — download a one-page PDF to share with family, police, or your bank

---

## 🧠 Why Gemma 4?

This project would not be possible without Gemma 4's specific combination of capabilities:

| Capability | Why It Matters for Sentinel |
|---|---|
| **Native multimodal vision** | Gemma 4 can directly read screenshots — no separate OCR step needed |
| **Thinking / reasoning mode** | Fraud detection requires multi-step reasoning, not just pattern matching — "why is this suspicious?" demands a reasoning chain |
| **128K context window** | Multiple pieces of evidence (screenshot + email + PDF) can be analysed together in one prompt |
| **Efficient MoE architecture** | The 27B MoE model activates only ~4B parameters per pass — fast enough to feel responsive despite running a large model |
| **Local/private deployment path** | The 4B variant runs entirely on-device — critical for fraud victims who cannot risk uploading sensitive financial screenshots to a cloud |

**Model used:** `google/gemma-4-27b-it` via OpenRouter (free tier)  
**Fallback:** `gemma-4-4b-it` via Gemini API (free tier, fully local option)

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- An [OpenRouter](https://openrouter.ai) account (free — no credit card required)
- A [Gemini API key](https://aistudio.google.com) (free — for fallback model)

### Installation

```bash
git clone https://github.com/yourusername/gemma-sentinel
cd gemma-sentinel
npm install
```

### Environment Setup

Create a `.env.local` file in the root:

```env
OPENROUTER_API_KEY=your_openrouter_key_here
GEMINI_API_KEY=your_gemini_api_key_here
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### Run Locally

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Deploy to Vercel

```bash
npm install -g vercel
vercel
```

Add your environment variables in the Vercel dashboard under Project Settings → Environment Variables.

---

## 🗂️ Project Structure

```
gemma-sentinel/
├── app/
│   ├── page.tsx              # Landing page + upload interface
│   ├── results/
│   │   └── page.tsx          # Verdict display page
│   └── api/
│       ├── analyse/
│       │   └── route.ts      # Main analysis endpoint (calls Gemma 4)
│       └── export/
│           └── route.ts      # PDF report generation
├── components/
│   ├── EvidenceUploader.tsx  # File/text/PDF ingestion UI
│   ├── VerdictCard.tsx       # Risk score + scam type display
│   ├── RedFlagsList.tsx      # Extracted red flags
│   ├── ReasoningPanel.tsx    # Gemma's plain-English reasoning
│   ├── Timeline.tsx          # Multi-evidence investigation timeline
│   └── ExportButton.tsx      # PDF download
├── lib/
│   ├── gemma.ts              # Gemma 4 API client (OpenRouter + Gemini)
│   ├── prompts.ts            # All system and analysis prompts
│   ├── parser.ts             # Structured output parser
│   └── imageToBase64.ts      # Image preprocessing utility
├── public/
│   └── demo/                 # Sample scam evidence for demo/testing
├── .env.local                # Never commit this
├── .env.example              # Commit this with placeholder values
└── README.md
```

---

## 🔍 How the Analysis Works

1. **Ingestion** — The uploaded file or pasted text is converted to the appropriate format (base64 for images, plain text for everything else).

2. **Prompt Construction** — A structured system prompt is assembled that instructs Gemma 4 to act as a fraud analysis expert, reason step-by-step, and return a structured JSON response.

3. **Gemma 4 Analysis** — The prompt + evidence is sent to Gemma 4 27B MoE. The model's thinking mode is enabled so it reasons through the evidence before generating its verdict.

4. **Structured Output Parsing** — The response is parsed into: `risk_score`, `scam_type`, `red_flags[]`, `reasoning`, `recommended_action`, `confidence`.

5. **Timeline Correlation** — If multiple inputs exist in the session, a second prompt asks Gemma to connect the evidence into a coherent attack narrative.

6. **Display** — Results are rendered in the verdict UI. Optionally exported as a PDF.

---

## 🧪 Testing with Sample Data

The `/public/demo/` folder contains anonymised sample evidence for testing:

| File | Type | Scam Type |
|---|---|---|
| `fake-bank-alert.png` | Screenshot | Fake GTBank transfer alert |
| `419-advance-fee.txt` | Text | Classic Nigerian advance-fee email |
| `fake-job-offer.txt` | Text | WhatsApp job scam message |
| `crypto-investment.png` | Screenshot | Fake crypto doubling scheme |
| `fake-invoice.pdf` | PDF | Fraudulent payment request |

You can also source your own test data — see [`DATA_SOURCES.md`](./DATA_SOURCES.md) for free datasets.

---

## 🛡️ Privacy

- Uploaded files are processed via a **stateless API call** — nothing is stored on any server
- The app does not log, save, or transmit your uploaded evidence beyond the analysis request
- For maximum privacy, swap the OpenRouter endpoint for a local Ollama instance running `gemma4:4b`

---

## 📦 Dependencies

```json
{
  "next": "14.x",
  "react": "18.x",
  "tailwindcss": "3.x",
  "openai": "4.x",
  "jspdf": "2.x",
  "@radix-ui/react-*": "latest"
}
```

---

## 🤝 Contributing

This project was built for a hackathon but contributions are welcome. Open an issue to discuss a feature before submitting a PR.

---

## 📄 License

MIT — see [LICENSE](./LICENSE)

---

## 🙏 Acknowledgements

- [Google DeepMind](https://deepmind.google) for the Gemma 4 model family
- [OpenRouter](https://openrouter.ai) for free API access
- [Mendeley SMS Phishing Dataset](https://data.mendeley.com/datasets/f45bkkt8pr/1) — Mishra & Soni (2020)
- [difraud benchmark](https://huggingface.co/datasets/difraud/difraud) — ReDAS Lab, University of Houston (2023)
- [CIRCL Phishing Screenshot Dataset](https://www.circl.lu/opendata/datasets/circl-phishing-dataset-01)
