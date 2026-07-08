# Gemma Sentinel

Gemma Sentinel is an offline-first, privacy-preserving fraud and scam analysis tool that detects deceptive patterns in messages, screenshots, and audio. It empowers users to instantly verify suspicious communications and protect themselves from financial loss without exposing their sensitive data to cloud servers.

## Tech Stack

- **Backend:** Python (3.10+), standard library (`http.server`)
- **Frontend:** Vanilla HTML5, CSS3, JavaScript (ES6 Modules)
- **AI Models:** Google Gemma 4 26B A4B (via Google Gemini API), Gemma 4 E4B (Local)
- **Inference Engine:** `llama.cpp` (`llama-server`)
- **Cloud/Deployment:** Render

## System Architecture

Gemma Sentinel operates via a stateless Python API and a vanilla web frontend. The system relies on a tiered, asymmetric analysis engine to prioritize privacy and fallback reliability:

1. **Google-hosted Gemma (`gemma-4-26b-a4b-it`)**: Primary engine for text and image evidence analysis, utilized when internet connectivity and API keys are available.
2. **Local Llama.cpp (`gemma-4-E4B-it`)**: The preferred privacy-first path. Executes text, image, and native audio analysis entirely on-device without external telemetry.
3. **Deterministic Rules Engine**: A local, regex-based heuristic fallback that triggers only if both AI models are unreachable, ensuring continuous protection.

No database is used. Evidence is kept in browser memory, sent only to the ephemeral `/api/analyse` endpoint, and never written to disk by the server.

## Prerequisites

- **Python**: 3.10 or higher.
- **Local Inference (Optional)**: `llama.cpp` (`llama-server`) for offline model execution.
- **Cloud Inference (Optional)**: Google AI Studio API key.

## Local Setup and Installation

1. **Clone the repository and set up the environment**:
   ```bash
   python -m venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   
   # On macOS/Linux:
   # source .venv/bin/activate
   ```

2. **Configure environment variables**:
   Create a `.env` file in the root directory (you can use the provided `.env.example` as a template):
   ```env
   MODEL_ENGINE=auto
   ENABLE_AUDIO=0
   GOOGLE_API_KEY=your_google_ai_studio_key
   GOOGLE_MODEL=gemma-4-26b-a4b-it
   GOOGLE_TIMEOUT=45
   LLAMACPP_ENABLED=1
   LLAMACPP_URL=http://127.0.0.1:8080
   LLAMACPP_MODEL=gemma-4-E4B-it
   LLAMACPP_TIMEOUT=60
   PORT=3000
   ```

3. **Start the application server**:
   ```bash
   python server.py
   ```
   The application will be available at `http://localhost:3000`.

4. **(Optional) Start the local Llama.cpp server**:
   For the preferred offline mode, run `llama-server` with the Gemma 4 E4B GGUF:
   ```bash
   llama-server -hf ggml-org/gemma-4-E4B-it-GGUF -c 8192 --host 127.0.0.1 --port 8080
   ```
   *Note: On low-RAM systems or Intel integrated graphics, prefer CPU-only mode by adding `-c 2048 -ngl 0 --device none --parallel 1 -b 256 -ub 128` to the command.*

## Usage Examples

**Via the Web Interface:**
Navigate to `http://localhost:3000`. You can paste text from a suspicious SMS or WhatsApp message, attach screenshots of fake bank alerts, and click "Analyse". The frontend will return a risk verdict (Low, Medium, High, Critical), identified red flags, and recommended actions.

**Via the API:**
```bash
curl -X POST http://localhost:3000/api/analyse \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": [
      {
        "type": "text",
        "name": "Suspicious SMS",
        "content": "Dear customer, your account is suspended. Verify your BVN immediately at http://bad-link.com"
      }
    ]
  }'
```

**Testing the Fallback Engine:**
To run the lightweight regression suite that tests the deterministic rules engine against common scam patterns:
```bash
python tests/test_rules.py
```

## Demo Assets

Sample text evidence lives in the `public/demo/text/` directory:
- `419-advance-fee-sample.txt`
- `smishing-account-suspended.txt`
- `fake-job-offer-whatsapp.txt`
- `crypto-investment-offer.txt`
- `mail-order-card-fraud.txt`
- `legitimate-bank-notice.txt`

When demonstrating with visual evidence, use sanitized screenshots. Ensure real phone numbers, account details, and private chat participants are not included.
