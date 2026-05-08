# Gemma Sentinel

Offline-first styled fraud and scam analysis demo powered by Gemma-compatible multimodal models.

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
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=google/gemma-4-27b-it
PORT=3000
```

If no API key is present, the app falls back to a local rule-based demo analyser so the interface remains usable without sending evidence anywhere.

## Privacy

Evidence is kept in browser memory, sent only to the local `/api/analyse` request, and never written to disk by the server. The server logs request metadata only, never message content or file data.
