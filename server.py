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
ONLINE_AUDIO_GEMMA_DEFAULT_BASE = "https://router.huggingface.co/v1"
LLAMACPP_CHAT_PATH = "/v1/chat/completions"
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

    has_audio = any(item["type"] == "audio" for item in inputs)

    if local_llamacpp_enabled():
        try:
            raw = call_llamacpp_gemma(inputs)
            verdict = parse_verdict(raw)
            verdict["timeline"] = build_timeline(inputs)
            verdict["mode"] = "gemma_llamacpp"
            verdict["notice"] = "Analysed with local Gemma through llama.cpp. Evidence stayed on this device."
            return verdict
        except (HTTPError, URLError, TimeoutError, ValueError):
            log("model_call_failed", provider="llamacpp")

    if has_audio and os.getenv("ONLINE_AUDIO_GEMMA_API_KEY"):
        try:
            raw = call_online_audio_gemma(inputs)
            verdict = parse_verdict(raw)
            verdict["timeline"] = build_timeline(inputs)
            verdict["mode"] = "gemma_audio_cloud"
            verdict["notice"] = "Audio was analysed by the configured hosted Gemma 4 E4B endpoint."
            return verdict
        except (HTTPError, URLError, TimeoutError, ValueError):
            log("model_call_failed", provider="online_audio_gemma")

    verdict = local_verdict(inputs)
    verdict["mode"] = "rules"
    verdict["notice"] = "Gemma was unavailable, so Sentinel used the deterministic last-resort rules engine."
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
        if kind == "audio" and content:
            mime_type = str(item.get("mimeType") or "")
            if re.match(r"^audio/(wav|wave|mpeg|mp3|mp4|m4a|webm|ogg|x-m4a)$", mime_type, re.I):
                clean.append({"type": "audio", "name": clean_name(item.get("name")), "content": content, "mimeType": mime_type})
    return clean


def clean_name(value: object) -> str:
    name = re.sub(r"[^\w .-]", "", str(value or "Evidence"))[:80].strip()
    return name or "Evidence"


def local_llamacpp_enabled() -> bool:
    return os.getenv("LLAMACPP_ENABLED", "1").lower() not in {"0", "false", "no", "off"}


def call_llamacpp_gemma(inputs: list[dict]) -> str:
    model = os.getenv("LLAMACPP_MODEL", "gemma-4-E4B-it")
    base_url = os.getenv("LLAMACPP_URL", "http://127.0.0.1:8080").rstrip("/")
    content = build_openai_multimodal_content(inputs, include_audio=True)
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0.1,
        "max_tokens": 1400,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("LLAMACPP_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = Request(
        f"{base_url}{LLAMACPP_CHAT_PATH}",
        data=body,
        method="POST",
        headers=headers,
    )
    with urlopen(request, timeout=int(os.getenv("LLAMACPP_TIMEOUT", "60"))) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("choices", [{}])[0].get("message", {}).get("content", "")


def call_online_audio_gemma(inputs: list[dict]) -> str:
    model = os.getenv("ONLINE_AUDIO_GEMMA_MODEL", "google/gemma-4-E4B-it:fastest")
    base_url = os.getenv("ONLINE_AUDIO_GEMMA_URL", ONLINE_AUDIO_GEMMA_DEFAULT_BASE).rstrip("/")
    content = build_openai_multimodal_content(inputs, include_audio=True)
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0.1,
        "max_tokens": 1400,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    request = Request(
        f"{base_url}/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {os.getenv('ONLINE_AUDIO_GEMMA_API_KEY')}",
            "Content-Type": "application/json",
        },
    )
    with urlopen(request, timeout=int(os.getenv("ONLINE_AUDIO_GEMMA_TIMEOUT", "60"))) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("choices", [{}])[0].get("message", {}).get("content", "")


def build_openai_multimodal_content(inputs: list[dict], include_audio: bool) -> list[dict]:
    content: list[dict] = [{"type": "text", "text": SYSTEM_PROMPT}]
    for index, item in enumerate(inputs, start=1):
        label = f"Evidence {index}: {item.get('name') or item['type']}"
        if item["type"] == "image":
            content.append({"type": "text", "text": f"--- {label} ({item['mimeType']}) ---"})
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{item['mimeType']};base64,{item['content']}"},
            })
        elif item["type"] == "audio" and include_audio:
            content.append({"type": "text", "text": f"--- {label} ({item['mimeType']}) ---\nTranscribe or interpret this short audio evidence, then include it in the fraud analysis."})
            content.append({
                "type": "input_audio",
                "input_audio": {"data": item["content"], "format": audio_format(item["mimeType"])},
            })
        elif item["type"] == "audio":
            content.append({"type": "text", "text": f"--- {label} ---\nAudio evidence was attached but this engine cannot inspect audio."})
        else:
            content.append({"type": "text", "text": f"--- {label} ---\n{item['content']}"})
    content.append({"type": "text", "text": "Analyse all evidence together as one case. Return only the JSON object."})
    return content


def audio_format(mime_type: str) -> str:
    if "mpeg" in mime_type or "mp3" in mime_type:
        return "mp3"
    if "mp4" in mime_type or "m4a" in mime_type:
        return "mp4"
    if "webm" in mime_type:
        return "webm"
    if "ogg" in mime_type:
        return "ogg"
    return "wav"


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
    joined = "\n".join(
        item["content"] if item["type"] == "text" else f"{item['name']} {item['type']} evidence"
        for item in inputs
    ).lower()
    evidence = score_rules(joined, inputs)
    flags = evidence["flags"]
    points = evidence["points"]
    risk_score = score_to_risk(points)
    return {
        "riskScore": risk_score,
        "riskPercentage": min(98, max(default_percent(risk_score), points)),
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
        "confidence": "medium" if any(item["type"] == "image" for item in inputs) else ("high" if points >= 70 else "medium"),
        "isScam": risk_score in {"high", "critical"},
        "timeline": build_timeline(inputs),
    }


def score_rules(text: str, inputs: list[dict]) -> dict:
    rules: list[tuple[int, str, str]] = [
        (34, r"\b(pay|send|transfer|deposit|wire|remit|western union|moneygram|bitcoin|usdt|gift card)\b.{0,90}\b(fee|activation|registration|processing|clearance|release|tax|charges?|stamp duty|courier|verification)\b", "It asks for a payment or fee before a promised benefit is released."),
        (30, r"\b(fee|activation|registration|processing|clearance|release|tax|charges?|stamp duty|courier|verification)\b.{0,90}\b(pay|send|transfer|deposit|wire|remit)\b", "It links a fee or charge to receiving money, documents, employment, or a prize."),
        (28, r"\b(inheritance|next of kin|beneficiary|unclaimed|abandoned|consignment|contract fund|over[- ]?invoiced|dormant account|foreign account|fund transfer)\b", "It uses classic advance-fee language around inheritance, beneficiaries, dormant accounts, or trapped funds."),
        (26, r"\b(i am|am|this is)\b.{0,80}\b(barrister|attorney|solicitor|bank manager|director|diplomat|minister|reverend|widow|orphan|prince|princess|doctor)\b", "It leans on a claimed authority or emotionally loaded identity."),
        (24, r"\b(central bank|cbn|efcc|firs|nnpc|chevron|shell|gtbank|access bank|uba|zenith|first bank|fbi|united nations|world bank|imf|customs)\b", "It invokes a trusted institution or brand that should be verified independently."),
        (22, r"\b(confidential|strictly confidential|keep this secret|do not disclose|private transaction|trust you|urgent assistance)\b", "It asks for secrecy or unusual trust, which protects the scammer from outside verification."),
        (22, r"\b(urgent|asap|immediately|within 24 hours|before friday|deadline|limited time|act now|reply now)\b", "It creates deadline pressure to stop careful verification."),
        (22, r"\b(won|winner|lottery|prize|grant|donation|compensation|approved loan|shortlisted|selected|investment opportunity|double your money|guaranteed profit)\b", "It uses a high-reward hook commonly seen in scam scripts."),
        (32, r"\b(account suspended|account has been suspended|verify your account|update your account|confirm your details|password|otp|one[- ]?time code|pin|bvn|nin|login)\b", "It asks for account verification or sensitive credentials."),
        (22, r"https?://|www\.|bit\.ly|tinyurl|t\.me/|wa\.me/|whatsapp|telegram|\+\d{7,}", "It includes external contact routes, links, or phone numbers that need independent verification."),
        (18, r"\b(kindly|dear friend|dearest|greetings|god fearing|good day|i need your assistance|mutually beneficial|percentage|share of the money)\b", "It contains phrasing common in 419-style social-engineering messages."),
        (16, r"\b(fake|receipt|alert|payment confirmation|successful transfer|pending transfer|release funds|activation code)\b", "It resembles fake payment-alert or fabricated receipt language."),
        (18, r"\b(mail order|credit card \(not paypal\)|credit card not paypal|not paypal|ups|fedex|united parcel service|shipping method|my clients|your products|sales sir|attention: ?sales)\b", "It resembles mail-order or reshipping fraud language around card payment and courier shipment."),
        (16, r"\b(invoice|purchase order|bank details|change of account|vendor|payment request|proforma)\b", "It contains invoice or payment-change language commonly abused in business fraud."),
        (14, r"\b(romance|love interest|online relationship|military|peacekeeping|hospital|medical emergency|stranded|customs hold)\b", "It contains emotional-pressure patterns used in romance and emergency scams."),
        (12, r"\b(crypto|bitcoin|forex|trading|mining|wallet|investment platform|roi|daily profit)\b", "It contains investment or crypto terminology often used in fraud offers."),
        (18, r"\b(chargeback|stolen card|card testing|velocity|multiple failed|device fingerprint|account age|synthetic identity|suspicious transaction|high[- ]risk merchant)\b", "It contains transaction-risk or account-fraud indicators."),
        (14, r"\b(fake review|paid review|review exchange|five star review|5 star review|verified purchase review|deceptive opinion|astroturf)\b", "It contains review manipulation or deceptive-opinion indicators."),
        (12, r"\b(fake news|misinformation|share before deleted|they do not want you to know|miracle cure|secret investment)\b", "It contains deceptive-content or misinformation signals."),
    ]

    points = 0
    flags: list[str] = []
    seen: set[str] = set()
    for weight, pattern, flag in rules:
        if re.search(pattern, text, re.I | re.S):
            points += weight
            if flag not in seen:
                flags.append(flag)
                seen.add(flag)

    if any(item["type"] == "image" for item in inputs):
        points += 28
        flags.append("Image evidence can contain forged logos, edited receipts, or manipulated screenshots; use Gemma vision for the real image read.")

    if any(item["type"] == "audio" for item in inputs):
        points += 28
        flags.append("Audio evidence can contain spoken impersonation, urgency, payment instructions, or voice-note scams; use local Gemma E4B/E2B audio for the real audio read.")

    if len(text) > 900 and re.search(r"\b(fund|bank|account|transfer|beneficiary|fee|urgent|confidential)\b", text):
        points += 12
        flags.append("The message is unusually long while steering toward money movement or secrecy, a common 419 pattern.")

    if re.search(r"\b(fee|charges?|tax|clearance|processing)\b", text) and re.search(r"\b(million|usd|dollars?|euro|euros?|pounds?|gbp|ngn|naira)\b|\$", text):
        points += 20
        flags.append("It combines a large promised amount with smaller fees or charges, a core advance-fee structure.")

    if re.search(r"\b(account suspended|verify your account|password|otp|pin|bvn|nin|login)\b", text) and re.search(r"https?://|www\.|bit\.ly|tinyurl|t\.me/|wa\.me/", text):
        points += 18
        flags.append("It combines account-security pressure with a link, a strong SMS phishing pattern.")

    if re.search(r"\b(crypto|bitcoin|forex|trading|investment|roi|profit)\b", text) and re.search(r"\b(guaranteed|double|activation|minimum|send|pay|deposit|whatsapp)\b", text):
        points += 18
        flags.append("It combines investment language with guaranteed returns or payment pressure.")

    if re.search(r"\b(nigeria|lagos|abuja)\b", text) and re.search(r"\b(credit card|not paypal|ups|fedex|united parcel service|shipping)\b", text) and re.search(r"\b(products?|order|sales|company|clients?)\b", text):
        points += 44
        flags.append("It combines overseas product ordering, card payment preference, and courier shipping, a known card-fraud/reshipping pattern.")

    if re.search(r"\b(romance|love interest|online relationship|military|peacekeeping|widow|stranded|hospital|medical emergency|customs hold)\b", text) and re.search(r"\b(send|pay|transfer|gift card|bitcoin|money|help|urgent|emergency)\b", text):
        points += 36
        flags.append("It combines emotional trust-building with a money or emergency request.")

    if re.search(r"\b(invoice|vendor|supplier|purchase order|payment request|bank details|account number)\b", text) and re.search(r"\b(change|new account|updated account|urgent payment|wire|transfer|remit)\b", text):
        points += 34
        flags.append("It combines invoice/vendor language with payment-detail changes or urgent transfer pressure.")

    if re.search(r"\b(transaction|amount|merchant|device|ip|account age|chargeback|failed login|failed attempt|velocity|synthetic identity)\b", text) and re.search(r"\b(csv|row|rows|multiple|high risk|unusual|suspicious|mismatch|new device|foreign ip)\b", text):
        points += 44
        flags.append("It describes transaction anomalies consistent with account or payment fraud review.")

    if re.search(r"\b(fake review|paid review|review exchange|five star|5 star|verified purchase|deceptive opinion|astroturf)\b", text) and re.search(r"\b(pay|refund|coupon|bulk|seller|listing|rating|positive)\b", text):
        points += 44
        flags.append("It combines review/rating language with payment, bulk activity, or seller manipulation.")

    return {"points": min(points, 100), "flags": flags[:8]}


def score_to_risk(points: int) -> str:
    if points >= 86:
        return "critical"
    if points >= 58:
        return "high"
    if points >= 28:
        return "medium"
    return "low"


def infer_scam_type(text: str, inputs: list[dict]) -> str:
    if re.search(r"\b(inheritance|next of kin|beneficiary|unclaimed|consignment|contract fund|dormant account|foreign account|fund transfer|barrister|widow|prince|princess)\b", text):
        return "419 advance-fee scam"
    if re.search(r"\b(job|shortlisted|salary|recruit|hr director)\b", text):
        return "Fake job offer / advance-fee fraud"
    if re.search(r"\b(crypto|bitcoin|investment|double)\b", text):
        return "Crypto investment scam"
    if re.search(r"\b(account suspended|verify your account|password|otp|pin|bvn|nin|login)\b", text):
        return "SMS phishing / credential theft"
    if re.search(r"\b(invoice|purchase order|change of account|vendor|payment request|proforma)\b", text):
        return "Invoice or business payment fraud"
    if re.search(r"\b(mail order|credit card \(not paypal\)|credit card not paypal|not paypal|ups|fedex|united parcel service|shipping method|my clients|your products|attention: ?sales)\b", text):
        return "Mail-order card fraud / reshipping scam"
    if re.search(r"\b(romance|love interest|online relationship|military|peacekeeping|widow|stranded|hospital|medical emergency|customs hold)\b", text):
        return "Romance or emergency assistance scam"
    if re.search(r"\b(transaction|chargeback|card testing|device fingerprint|account age|synthetic identity|suspicious transaction)\b", text):
        return "Bank account or transaction fraud"
    if re.search(r"\b(fake review|paid review|review exchange|five star review|5 star review|verified purchase review|deceptive opinion|astroturf)\b", text):
        return "Review or deceptive-content fraud"
    if re.search(r"\b(fake news|misinformation|share before deleted|miracle cure|secret investment)\b", text):
        return "Deceptive content / misinformation"
    if re.search(r"\b(bank|transfer|alert|gtbank|access bank|uba|opay|palmpay)\b", text) or any(item["type"] == "image" for item in inputs):
        return "Fake bank alert / payment scam"
    if re.search(r"\b(lottery|prize|grant|donation|compensation)\b", text):
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
