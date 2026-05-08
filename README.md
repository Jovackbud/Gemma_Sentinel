# Gemma Sentinel

Offline-first styled fraud and scam analysis demo powered by Gemma-compatible multimodal models.

## Why Gemma 4?

Gemma Sentinel is built for the DEV Gemma 4 Challenge "Build With Gemma 4" track. The product goal is simple: let someone point a private AI analyst at a suspicious screenshot, WhatsApp message, SMS, email, or document text and get a grounded fraud verdict without turning their evidence into a permanent cloud record.

Gemma 4 is the right model family for this because the project needs three capabilities at once:

1. **Native multimodal understanding**: Scam evidence is often visual or spoken. Fake bank alerts, forged receipts, phishing pages, WhatsApp screenshots, and voice notes contain clues that keyword filters miss.
2. **Reasoning-first output**: A fraud tool must explain why something is suspicious. Gemma's value here is not just classification; it is producing user-verifiable red flags and plain-English next steps.
3. **Local deployment path**: Fraud victims may be handling bank screenshots, identity details, OTP bait, invoices, or family conversations. Gemma's edge-capable variants make a private/offline mode realistic for low-connectivity areas and privacy-sensitive users.

The intended model strategy is:

- **Local Gemma 4 E4B through llama.cpp** for the preferred private path: text, image, and native audio support with a minimal local runtime and no background model registry requirement.
- **Hosted Gemma 4 E4B** for online text, image, and audio analysis when the user cannot run the model locally.
- **Deterministic rules** only as a last-resort safety net when no model is reachable.

This project deliberately avoids a heavy framework stack so the submission emphasizes Gemma 4 doing real work at the center, not infrastructure theater around it.

This implementation is intentionally lean:

- No frontend framework
- No build step
- No runtime dependencies
- Stateless Python API using the standard library only
- No server-side file storage
- No sensitive evidence logging

## Run

```bash
python -m venv .venv
.venv\Scripts\python server.py
```

Open http://localhost:3000.

## Environment

```env
LLAMACPP_ENABLED=1
LLAMACPP_URL=http://127.0.0.1:8080
LLAMACPP_MODEL=gemma-4-E4B-it
LLAMACPP_TIMEOUT=60
ONLINE_AUDIO_GEMMA_API_KEY=your_hosted_gemma_4_e4b_key
ONLINE_AUDIO_GEMMA_URL=https://router.huggingface.co/v1
ONLINE_AUDIO_GEMMA_MODEL=google/gemma-4-E4B-it:fastest
ONLINE_AUDIO_GEMMA_TIMEOUT=60
PORT=3000
```

Analysis order:

1. Local Gemma 4 E4B through llama.cpp at `LLAMACPP_URL`.
2. Hosted Gemma 4 E4B through `ONLINE_AUDIO_GEMMA_*`.
3. Deterministic rules engine as the last-resort fallback.

For preferred offline use, run `llama-server` with Gemma 4 E4B GGUF:

```bash
llama-server -hf ggml-org/gemma-4-E4B-it-GGUF -c 8192 --host 127.0.0.1 --port 8080
```

Gemma 4 E4B and E2B support native audio input. This app standardizes on Gemma 4 E4B for both online and offline model paths so text, image, and audio follow the same conceptual pipeline.

For hosted audio mode, configure an OpenAI-compatible provider that exposes Gemma 4 E4B audio support. The default shape targets Hugging Face's OpenAI-compatible router:

```env
ONLINE_AUDIO_GEMMA_API_KEY=your_huggingface_token
ONLINE_AUDIO_GEMMA_URL=https://router.huggingface.co/v1
ONLINE_AUDIO_GEMMA_MODEL=google/gemma-4-E4B-it:fastest
```

The local model path keeps evidence on the device and is the preferred mode for edge devices, low-connectivity environments, and sensitive evidence.

## Demo Assets

Sample text evidence lives in `public/demo/text/`:

- `419-advance-fee-sample.txt`
- `smishing-account-suspended.txt`
- `fake-job-offer-whatsapp.txt`
- `crypto-investment-offer.txt`
- `mail-order-card-fraud.txt`
- `legitimate-bank-notice.txt`

Use your own sanitized screenshots for the visual demo. Do not include real phone numbers, account numbers, names, or private chat participants in public assets.

## Regression Check

Run the lightweight fallback regression suite:

```bash
.venv\Scripts\python tests\test_rules.py
```

This checks that the last-resort rules engine still catches representative 419, smishing, fake job, crypto, mail-order card fraud, romance/emergency, invoice/BEC, transaction anomaly, review manipulation, and screenshot fallback patterns.

## Coverage Target

Gemma is the primary detector. The deterministic rules engine is only the final fallback, but it is regression-tested against these dataset families:

| Source family | Coverage target |
|---|---|
| Mendeley SMS Phishing | Account suspension, OTP/BVN/PIN, credential links, urgency |
| 419scam.org | Advance-fee, beneficiary/inheritance, mail-order card fraud, secrecy pressure |
| difraud | Phishing, job scams, romance fraud, deceptive reviews/opinions, spam-like fraud hooks |
| CIRCL screenshots | Routed to Gemma vision; rules fallback raises caution on image-only evidence |
| Kaggle bank account fraud | Transaction anomaly text/CSV patterns, card testing, chargeback, velocity, new-device risk |
| User-supplied screenshots/audio | Routed to Gemma multimodal analysis with any pasted text analysed in the same evidence batch |

## Privacy

Evidence is kept in browser memory, sent only to the local `/api/analyse` request, and never written to disk by the server. The server logs request metadata only, never message content or file data.
