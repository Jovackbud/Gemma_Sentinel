from __future__ import annotations

import json
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
PUBLIC_DIR = ROOT / "public"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
MAX_BODY_BYTES = 12 * 1024 * 1024

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".txt": "text/plain; charset=utf-8",
}

SYSTEM_PROMPT = """
You are Gemma Sentinel, a privacy-preserving fraud and scam detection analyst with deep knowledge of Nigerian and West African scam patterns.

Analyse the supplied evidence. Evidence may include screenshots or text. Be careful, specific, and honest about uncertainty.

Return valid JSON only:
{
  "riskScore": "low" | "medium" | "high" | "critical",
  "riskPercentage": <number 0-100>,
  "scamType": "<specific scam type>",
  "redFlags": ["<specific red flag>"],
  "reasoning": "<2-4 plain-English sentences>",
  "recommendedAction": "<clear next step>",
  "confidence": "low" | "medium" | "high",
  "isScam": true | false
}

Watch for advance fees, fake bank alerts, fake jobs, impersonation of trusted institutions, urgency, requests for codes, suspicious links, forged screenshots, crypto doubling schemes, and emotional manipulation. Do not reveal hidden chain-of-thought; provide concise reasons only.
"""


def main() -> None:
    load_local_env()
    port = int(os.getenv("PORT", "3000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    log("server_started", port=port, url=f"http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("server_stopped")


class Handler(BaseHTTPRequestHandler):
    server_version = "GemmaSentinel/0.1"

    def log_message(self, _format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        if self.path == "/":
            self.serve_static("/index.html")
            return
        self.serve_static(self.path.split("?", 1)[0])

    def do_POST(self) -> None:
        started = time.time()
        if self.path.split("?", 1)[0] != "/api/analyse":
            self.send_json(404, {"error": "Not found"})
            return

        try:
            payload = self.read_json()
            verdict = analyse_evidence(payload)
            self.send_json(200, verdict)
            log("analysis_completed", ms=int((time.time() - started) * 1000), mode=verdict.get("mode"))
        except PublicError as error:
            self.send_json(error.status, {"error": error.message})
            log("request_failed", status=error.status, message=error.code)
        except Exception:
            self.send_json(500, {"error": "Request failed."})
            log("request_failed", status=500, message="internal_error")

    def read_json(self) -> dict:
        length = int(self.headers.get("content-length", "0") or "0")
        if length > MAX_BODY_BYTES:
            raise PublicError(413, "Evidence is too large.", "payload_too_large")
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            raise PublicError(400, "Invalid request body.", "invalid_json")

    def serve_static(self, request_path: str) -> None:
        safe = Path(request_path.lstrip("/"))
        target = (PUBLIC_DIR / safe).resolve()
        if PUBLIC_DIR not in target.parents and target != PUBLIC_DIR:
            self.send_json(403, {"error": "Forbidden"})
            return
        if not target.exists() or not target.is_file():
            self.send_json(404, {"error": "Not found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(target.suffix, "application/octet-stream"))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(target.read_bytes())

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class PublicError(Exception):
    def __init__(self, status: int, message: str, code: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.code = code


def analyse_evidence(payload: dict) -> dict:
    inputs = normalise_inputs(payload.get("inputs") if isinstance(payload, dict) else None)
    if not inputs:
        raise PublicError(400, "No evidence provided.", "no_evidence")

    if not os.getenv("OPENROUTER_API_KEY"):
        verdict = local_verdict(inputs)
        verdict["mode"] = "local"
        return verdict

    try:
        raw = call_openrouter(inputs)
        verdict = parse_verdict(raw)
        verdict["timeline"] = build_timeline(inputs)
        verdict["mode"] = "gemma"
        return verdict
    except (HTTPError, URLError, TimeoutError, ValueError):
        verdict = local_verdict(inputs)
        verdict["mode"] = "local_fallback"
        verdict["notice"] = "The model provider was unavailable, so Sentinel used the private local fallback."
        log("model_call_failed", message="provider_unavailable")
        return verdict


def normalise_inputs(inputs: object) -> list[dict]:
    if not isinstance(inputs, list):
        return []
    clean: list[dict] = []
    for item in inputs[:6]:
        if not isinstance(item, dict):
            continue
        kind = item.get("type")
        content = str(item.get("content") or "").strip()
        if kind == "text" and content:
            clean.append({"type": "text", "name": clean_name(item.get("name")), "content": content[:50000]})
        if kind == "image" and content:
            mime_type = str(item.get("mimeType") or "")
            if re.match(r"^image/(png|jpe?g|webp)$", mime_type, re.I):
                clean.append({"type": "image", "name": clean_name(item.get("name")), "content": content, "mimeType": mime_type})
    return clean


def clean_name(value: object) -> str:
    name = re.sub(r"[^\w .-]", "", str(value or "Evidence"))[:80].strip()
    return name or "Evidence"


def call_openrouter(inputs: list[dict]) -> str:
    content: list[dict] = [{"type": "text", "text": SYSTEM_PROMPT}]
    for index, item in enumerate(inputs, start=1):
        label = f"Evidence {index}: {item.get('name') or item['type']}"
        if item["type"] == "image":
            content.append({"type": "text", "text": f"--- {label} ({item['mimeType']}) ---"})
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{item['mimeType']};base64,{item['content']}"},
            })
        else:
            content.append({"type": "text", "text": f"--- {label} ---\n{item['content']}"})
    content.append({"type": "text", "text": "Return only the JSON object."})

    body = json.dumps({
        "model": os.getenv("OPENROUTER_MODEL", "google/gemma-4-27b-it"),
        "messages": [{"role": "user", "content": content}],
        "temperature": 0.1,
        "max_tokens": 1600,
    }).encode("utf-8")

    request = Request(
        f"{OPENROUTER_BASE}/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("APP_URL", f"http://localhost:{os.getenv('PORT', '3000')}"),
            "X-Title": "Gemma Sentinel",
        },
    )
    with urlopen(request, timeout=35) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("choices", [{}])[0].get("message", {}).get("content", "")


def parse_verdict(raw_text: str) -> dict:
    cleaned = str(raw_text or "").replace("```json", "").replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        return local_verdict([])
    try:
        return validate_verdict(json.loads(cleaned[start:end + 1]))
    except json.JSONDecodeError:
        return local_verdict([])


def validate_verdict(value: dict) -> dict:
    risk_scores = {"low", "medium", "high", "critical"}
    confidence_values = {"low", "medium", "high"}
    risk_score = value.get("riskScore") if value.get("riskScore") in risk_scores else "medium"
    return {
        "riskScore": risk_score,
        "riskPercentage": clamp(value.get("riskPercentage"), 0, 100, default_percent(risk_score)),
        "scamType": clean_text(value.get("scamType"), "Unclear"),
        "redFlags": [clean_text(flag, "") for flag in value.get("redFlags", []) if clean_text(flag, "")][:8],
        "reasoning": clean_text(value.get("reasoning"), "The evidence needs independent verification before you trust it."),
        "recommendedAction": clean_text(value.get("recommendedAction"), "Verify through an official channel before responding or sending money."),
        "confidence": value.get("confidence") if value.get("confidence") in confidence_values else "medium",
        "isScam": bool(value.get("isScam", risk_score in {"high", "critical"})),
    }


def local_verdict(inputs: list[dict]) -> dict:
    joined = "\n".join(item["content"] if item["type"] == "text" else f"{item['name']} image evidence" for item in inputs).lower()
    flags: list[str] = []

    if re.search(r"\b(pay|send|transfer|deposit)\b.+\b(fee|activation|registration|processing|release)\b", joined):
        flags.append("It asks for an upfront fee before releasing money, a job, or a benefit.")
    if re.search(r"\b(urgent|asap|before friday|limited|immediately|now)\b", joined):
        flags.append("It creates deadline pressure to stop careful verification.")
    if re.search(r"\b(whatsapp|telegram|dm)\b", joined):
        flags.append("It moves the conversation to informal channels that are harder to verify.")
    if re.search(r"\b(chevron|nnpc|cbn|efcc|firs|gtbank|access bank|uba|opay|palmpay)\b", joined):
        flags.append("It invokes a trusted institution or brand that should be verified independently.")
    if re.search(r"\b(won|prize|lottery|shortlisted|investment|double|crypto|inheritance)\b", joined):
        flags.append("It uses a high-reward hook commonly seen in scam scripts.")
    if any(item["type"] == "image" for item in inputs):
        flags.append("Image evidence can contain forged logos, edited receipts, or manipulated screenshots.")

    risk_score = "critical" if len(flags) >= 5 else "high" if len(flags) >= 3 else "medium" if flags else "low"
    return {
        "riskScore": risk_score,
        "riskPercentage": default_percent(risk_score),
        "scamType": infer_scam_type(joined, inputs),
        "redFlags": flags or ["No strong local rule matched, but independent verification is still recommended."],
        "reasoning": (
            "The provided evidence does not match the strongest local scam patterns in the private fallback analyser. Treat this as a preliminary screen, not a final guarantee."
            if risk_score == "low"
            else "The evidence matches multiple social-engineering patterns used in Nigerian and West African fraud: pressure, trusted-name impersonation, and value-before-verification. Do not treat the sender's claim as real until you verify it through an official channel you found yourself."
        ),
        "recommendedAction": (
            "Verify using an official website, branch, or known phone number before taking action."
            if risk_score == "low"
            else "Do not pay, click links, or share codes. Save the evidence, block the sender, and report through your bank or relevant authority."
        ),
        "confidence": "medium" if any(item["type"] == "image" for item in inputs) else "high",
        "isScam": risk_score in {"high", "critical"},
        "timeline": build_timeline(inputs),
    }


def infer_scam_type(text: str, inputs: list[dict]) -> str:
    if re.search(r"\b(job|shortlisted|salary|recruit|hr director)\b", text):
        return "Fake job offer / advance-fee fraud"
    if re.search(r"\b(crypto|bitcoin|investment|double)\b", text):
        return "Crypto investment scam"
    if re.search(r"\b(bank|transfer|alert|gtbank|access bank|uba|opay|palmpay)\b", text) or any(item["type"] == "image" for item in inputs):
        return "Fake bank alert / payment scam"
    if re.search(r"\b(inheritance|beneficiary|lottery|prize|fund)\b", text):
        return "419 advance-fee scam"
    return "Suspicious message or document"


def build_timeline(inputs: list[dict]) -> dict | None:
    if len(inputs) < 2:
        return None
    return {
        "areConnected": True,
        "connectionReason": "Multiple pieces of evidence in one session share enough context to review as one case.",
        "attackNarrative": "The contact appears to build credibility first, then increase pressure toward payment, disclosure, or account action. Review each step as part of the same persuasion chain until proven otherwise.",
        "ultimateGoal": "Money, account access, identity details, or trust escalation.",
        "urgencyLevel": "escalating",
    }


def default_percent(risk_score: str) -> int:
    return {"low": 18, "medium": 52, "high": 78, "critical": 94}.get(risk_score, 50)


def clean_text(value: object, fallback: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:1200] if text else fallback


def clamp(value: object, minimum: int, maximum: int, fallback: int) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return fallback
    return min(maximum, max(minimum, number))


def load_local_env() -> None:
    for name in (".env.local", ".env"):
        path = ROOT / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def log(event: str, **fields: object) -> None:
    print(json.dumps({"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event, **fields}), flush=True)


if __name__ == "__main__":
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10+ is required.")
    main()
