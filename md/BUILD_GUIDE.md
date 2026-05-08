# Gemma Sentinel — Architecture & Build Guide

*Everything a developer needs to understand the system design and build the MVP.*

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser (Client)                      │
│                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│   │  Evidence    │    │  Analysis    │    │  Verdict     │  │
│   │  Uploader    │───▶│  Loading     │───▶│  Display     │  │
│   │  Component   │    │  State       │    │  Component   │  │
│   └──────────────┘    └──────────────┘    └──────────────┘  │
│          │                                        │          │
│    FileReader API                          PDF Export        │
│    (base64 encode)                         (jsPDF)           │
└──────────────────────────────────────────────────────────────┘
          │                                        ▲
          ▼                                        │
┌─────────────────────────────────────────────────────────────┐
│                     Next.js API Routes                       │
│                                                              │
│   POST /api/analyse          POST /api/export               │
│   ┌─────────────────┐        ┌─────────────────┐            │
│   │ 1. Parse input  │        │ Format report   │            │
│   │ 2. Build prompt │        │ Return PDF      │            │
│   │ 3. Call Gemma 4 │        └─────────────────┘            │
│   │ 4. Parse output │                                        │
│   │ 5. Return JSON  │                                        │
│   └─────────────────┘                                        │
└──────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Gemma 4 (via OpenRouter)                    │
│                                                              │
│   Model: google/gemma-4-27b-it                              │
│   Mode:  Thinking enabled (reasoning mode)                  │
│   Context: 128K tokens                                       │
│   Multimodal: Vision + Text                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Core Files to Build

### `lib/gemma.ts` — The Model Client

```typescript
const OPENROUTER_BASE = "https://openrouter.ai/api/v1";

export interface AnalysisInput {
  type: "text" | "image" | "pdf";
  content: string; // text body or base64 string
  mimeType?: string;
}

export interface SentinelVerdict {
  riskScore: "low" | "medium" | "high" | "critical";
  riskPercentage: number;
  scamType: string;
  redFlags: string[];
  reasoning: string;
  recommendedAction: string;
  confidence: "low" | "medium" | "high";
}

export async function analyseEvidence(
  inputs: AnalysisInput[]
): Promise<SentinelVerdict> {
  const messages = buildMessages(inputs);

  const response = await fetch(`${OPENROUTER_BASE}/chat/completions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
      "Content-Type": "application/json",
      "HTTP-Referer": process.env.NEXT_PUBLIC_APP_URL || "",
      "X-Title": "Gemma Sentinel",
    },
    body: JSON.stringify({
      model: "google/gemma-4-27b-it",
      messages,
      temperature: 0.1, // Low temp for consistent structured output
      max_tokens: 2048,
    }),
  });

  const data = await response.json();
  const rawText = data.choices[0].message.content;
  return parseVerdict(rawText);
}

function buildMessages(inputs: AnalysisInput[]) {
  const contentBlocks: any[] = [
    {
      type: "text",
      text: SYSTEM_PROMPT,
    },
  ];

  for (const input of inputs) {
    if (input.type === "image") {
      contentBlocks.push({
        type: "image_url",
        image_url: {
          url: `data:${input.mimeType};base64,${input.content}`,
        },
      });
    } else {
      contentBlocks.push({
        type: "text",
        text: `--- EVIDENCE (${input.type.toUpperCase()}) ---\n${input.content}`,
      });
    }
  }

  contentBlocks.push({
    type: "text",
    text: "Analyse all evidence above. Return your analysis as valid JSON matching the schema in the system prompt.",
  });

  return [{ role: "user", content: contentBlocks }];
}
```

---

### `lib/prompts.ts` — The Prompting Strategy

The prompt is the most important engineering decision in this project. It must:
1. Instruct Gemma to reason step-by-step (activating thinking mode)
2. Return structured JSON (for reliable parsing)
3. Be grounded in West African scam patterns (for local relevance)

```typescript
export const SYSTEM_PROMPT = `
You are Gemma Sentinel, an expert fraud and scam detection analyst with deep knowledge of:
- Nigerian advance-fee fraud (419 scams)
- West African financial scams (fake bank alerts, fake GTBank/Access Bank/UBA transfers)
- WhatsApp and SMS phishing patterns common in Nigeria and West Africa
- International phishing, job scam, romance scam, and crypto fraud patterns
- Visual forgery detection (fake logos, inconsistent fonts, fabricated screenshots)

Your task is to analyse the provided evidence (which may include screenshots, text messages, emails, or documents) and produce a structured fraud assessment.

REASONING APPROACH:
1. First, carefully examine all provided evidence
2. List every suspicious element you notice (visual, linguistic, structural, psychological)
3. Classify the type of scam if present
4. Assess risk level based on: severity of deception, financial risk to victim, specificity of targeting
5. Formulate a plain-English explanation suitable for a non-technical user

RETURN YOUR RESPONSE AS VALID JSON WITH THIS EXACT SCHEMA:
{
  "riskScore": "low" | "medium" | "high" | "critical",
  "riskPercentage": <number 0-100>,
  "scamType": "<specific scam type name>",
  "redFlags": ["<flag 1>", "<flag 2>", ...],
  "reasoning": "<2-4 sentence plain English explanation of why this is or isn't a scam>",
  "recommendedAction": "<clear instruction for the user>",
  "confidence": "low" | "medium" | "high",
  "isScam": true | false
}

RISK SCORE GUIDELINES:
- "low": Likely legitimate, minor concerns
- "medium": Suspicious elements present, proceed with caution
- "high": Strong indicators of fraud, do not engage
- "critical": Clear, definitive fraud — immediate action required

COMMON WEST AFRICAN SCAM PATTERNS TO WATCH FOR:
- Fake bank transfer alerts asking for "activation fee" to release funds
- "You have won" lottery/prize messages requiring payment to claim
- Fake job offers from "oil companies" or "government agencies" requiring upfront fees
- Romance scams building trust before requesting money for emergencies
- Crypto investment "doubling" schemes
- Impersonation of EFCC, FIRS, CBN, or NNPC officials
- WhatsApp "wrong number" scams that escalate to investment fraud

Return ONLY the JSON object. No preamble, no explanation outside the JSON.
`;

export const TIMELINE_PROMPT = `
You are analysing multiple pieces of evidence that may be connected parts of a single scam operation.

Review all evidence provided and determine:
1. Are these pieces connected (same scammer, same operation)?
2. What is the attack progression / timeline?
3. What is the scammer's ultimate goal?

Return as JSON:
{
  "areConnected": true | false,
  "connectionReason": "<explanation>",
  "attackNarrative": "<2-3 sentence story of the attack from the scammer's perspective>",
  "ultimateGoal": "<what they were trying to get>",
  "urgencyLevel": "building" | "peak" | "escalating"
}
`;
```

---

### `lib/parser.ts` — Output Parser

Gemma 4 is instructed to return JSON but may occasionally wrap it. Parse defensively:

```typescript
export function parseVerdict(rawText: string): SentinelVerdict {
  // Strip markdown code fences if present
  const cleaned = rawText
    .replace(/```json\n?/g, "")
    .replace(/```\n?/g, "")
    .trim();

  // Find JSON object boundaries
  const start = cleaned.indexOf("{");
  const end = cleaned.lastIndexOf("}") + 1;
  const jsonStr = cleaned.slice(start, end);

  try {
    const parsed = JSON.parse(jsonStr);
    return validateAndNormalise(parsed);
  } catch (e) {
    // Fallback: return a safe default with error flag
    return {
      riskScore: "medium",
      riskPercentage: 50,
      scamType: "Unable to determine",
      redFlags: ["Analysis error — please try again"],
      reasoning: "The analysis could not be completed. Please try uploading again.",
      recommendedAction: "Try again with a clearer image or more complete text.",
      confidence: "low",
    };
  }
}

function validateAndNormalise(parsed: any): SentinelVerdict {
  const validRiskScores = ["low", "medium", "high", "critical"];
  const validConfidence = ["low", "medium", "high"];

  return {
    riskScore: validRiskScores.includes(parsed.riskScore)
      ? parsed.riskScore
      : "medium",
    riskPercentage: Math.min(100, Math.max(0, Number(parsed.riskPercentage) || 50)),
    scamType: String(parsed.scamType || "Unknown"),
    redFlags: Array.isArray(parsed.redFlags) ? parsed.redFlags : [],
    reasoning: String(parsed.reasoning || ""),
    recommendedAction: String(parsed.recommendedAction || ""),
    confidence: validConfidence.includes(parsed.confidence)
      ? parsed.confidence
      : "medium",
  };
}
```

---

### `app/api/analyse/route.ts` — The API Endpoint

```typescript
import { NextRequest, NextResponse } from "next/server";
import { analyseEvidence } from "@/lib/gemma";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const inputs = [];

    // Handle text input
    const text = formData.get("text") as string;
    if (text?.trim()) {
      inputs.push({ type: "text" as const, content: text });
    }

    // Handle file upload
    const file = formData.get("file") as File;
    if (file) {
      const bytes = await file.arrayBuffer();
      const base64 = Buffer.from(bytes).toString("base64");

      if (file.type.startsWith("image/")) {
        inputs.push({
          type: "image" as const,
          content: base64,
          mimeType: file.type,
        });
      } else if (file.type === "application/pdf") {
        // Extract text from PDF — use pdf-parse
        const pdfParse = await import("pdf-parse");
        const parsed = await pdfParse.default(Buffer.from(bytes));
        inputs.push({ type: "pdf" as const, content: parsed.text });
      }
    }

    if (inputs.length === 0) {
      return NextResponse.json(
        { error: "No evidence provided" },
        { status: 400 }
      );
    }

    const verdict = await analyseEvidence(inputs);
    return NextResponse.json(verdict);
  } catch (error) {
    console.error("Analysis error:", error);
    return NextResponse.json(
      { error: "Analysis failed" },
      { status: 500 }
    );
  }
}
```

---

## UI Component Checklist

### `EvidenceUploader.tsx`
- Drag-and-drop zone for image/PDF files
- Text area for pasting messages
- Clear "No files are stored" privacy notice
- File type validation (PNG, JPG, WEBP, PDF only)
- File size limit (10MB)
- Loading state after submit

### `VerdictCard.tsx`
- Large colour-coded risk badge: green/yellow/orange/red
- Risk percentage with circular progress indicator
- Scam type label with icon
- Confidence indicator (so users can calibrate trust)

### `RedFlagsList.tsx`
- Numbered list of specific red flags
- Each flag should be one short, specific sentence
- Expandable if > 5 flags

### `ReasoningPanel.tsx`
- The centrepiece component
- Gemma's plain-English reasoning paragraph
- Should feel like reading an expert's note
- Add a subtle "Gemma's Analysis" header

### `Timeline.tsx` (multi-evidence)
- Only shows when 2+ inputs have been analysed
- Visual timeline with connected nodes
- Attack narrative paragraph
- "Ultimate goal" callout box

### `ExportButton.tsx`
- Generates a one-page PDF
- Includes: timestamp, inputs summary, verdict, red flags, reasoning, recommended action
- "Download Report" button with PDF icon

---

## Environment Variables

```env
# .env.local (never commit)
OPENROUTER_API_KEY=sk-or-...
GEMINI_API_KEY=AIza...
NEXT_PUBLIC_APP_URL=http://localhost:3000

# .env.example (commit this)
OPENROUTER_API_KEY=your_openrouter_key
GEMINI_API_KEY=your_gemini_api_key
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

## Getting Free API Access

### OpenRouter (Primary — Gemma 4 27B MoE)

1. Go to https://openrouter.ai/
2. Sign up with email (no credit card required)
3. Navigate to Keys → Create Key
4. Free tier includes access to `google/gemma-4-27b-it`
5. Check current free tier limits at https://openrouter.ai/models

### Gemini API (Fallback — Gemma 4 4B)

1. Go to https://aistudio.google.com/
2. Sign in with Google account
3. Click "Get API Key"
4. Free tier: 15 requests/minute, 1,500 requests/day
5. Access Gemma 4 models via the Gemini API endpoint

---

## Local Development with Ollama (Zero Cost, Maximum Privacy)

To run Gemma 4 entirely locally with no API calls:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull Gemma 4 4B (requires ~8GB RAM)
ollama pull gemma4:4b

# Start Ollama server
ollama serve
```

Then update your `lib/gemma.ts` to point to `http://localhost:11434/api/chat` instead of OpenRouter. The request format uses the OpenAI-compatible endpoint Ollama exposes.

This is the "fully local, zero cloud" mode that you can demo for maximum privacy narrative impact.

---

## Deployment

### Vercel (Recommended — Free Tier)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables
vercel env add OPENROUTER_API_KEY
vercel env add GEMINI_API_KEY
vercel env add NEXT_PUBLIC_APP_URL
```

Your live URL will be something like `https://gemma-sentinel.vercel.app`.

### Important Vercel Settings

- Function timeout: Set to 30 seconds (API routes → Functions tab in Vercel dashboard)
- The default 10-second timeout will cause Gemma analysis to fail on slow requests

---

## Testing Checklist

Before recording your demo video, test each of these:

- [ ] Text-only analysis completes without error
- [ ] PNG screenshot analysis completes and shows visual reasoning
- [ ] JPEG screenshot works
- [ ] PDF analysis works (text extracted and analysed)
- [ ] Multi-evidence (text + image) produces Investigation Timeline
- [ ] PDF report downloads correctly
- [ ] Works on mobile (responsive)
- [ ] Works in Chrome, Firefox, Safari
- [ ] Error state shows gracefully (test with corrupted file)
- [ ] API rate limit handled gracefully (shows friendly message)
- [ ] All three demo scenarios produce convincing, correct verdicts

---

## Known Edge Cases

| Edge Case | Behaviour |
|---|---|
| Very low-res screenshot | Gemma may not read text clearly; show "low confidence" |
| Legitimate message uploaded | Risk score should be "low"; reasoning should explain it's likely real |
| Non-English text (Yoruba, Igbo, Pidgin) | Gemma 4 handles 140+ languages; should work but test explicitly |
| Huge PDF (100+ pages) | Truncate to first 50,000 tokens; add notice in UI |
| OpenRouter rate limit hit | Show "Analysis temporarily unavailable, try again in a moment" |
| User uploads a photo of a person | Out of scope; return "This doesn't appear to be scam evidence — please upload a message or document" |
