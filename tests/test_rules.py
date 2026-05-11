from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import server  # noqa: E402


CASES = [
    (
        "419 advance-fee",
        "I am Barrister John representing a deceased client with unclaimed fund of USD 10.5 million. "
        "You are next of kin beneficiary. This is strictly confidential. Send processing fee to release the funds urgently.",
        "critical",
        "419 advance-fee scam",
    ),
    (
        "SMS phishing",
        "Your bank account has been suspended. Verify your BVN and OTP now at http://bad.example to restore access.",
        "high",
        "SMS phishing / credential theft",
    ),
    (
        "Fake job fee",
        "Good afternoon. Chevron shortlisted you for a job. Pay registration fee before Friday ASAP.",
        "critical",
        "Fake job offer / advance-fee fraud",
    ),
    (
        "Crypto doubling",
        "Double your bitcoin in 48 hours. Guaranteed profit. Send NGN 50000 activation payment on WhatsApp.",
        "high",
        "Crypto investment scam",
    ),
    (
        "Mail-order card fraud",
        "ATTENTION: SALES Sir/madam, my clients saw your address on the internet and are interested in your products. "
        "They are situated in Nigeria. Payment option is through credit card not PayPal and shipping is via UPS or FedEx express.",
        "high",
        "Mail-order card fraud / reshipping scam",
    ),
    (
        "Romance emergency scam",
        "I love you and want to be with you, but I am stranded at customs after peacekeeping travel. "
        "Please send money urgently by gift card so I can leave the hospital and come home.",
        "high",
        "Romance or emergency assistance scam",
    ),
    (
        "Invoice payment change",
        "Please process this vendor invoice today. Our bank details have changed, so make urgent payment by wire transfer to the new account number below.",
        "high",
        "Invoice or business payment fraud",
    ),
    (
        "Bank transaction anomaly",
        "CSV rows show multiple suspicious transaction attempts from a new device and foreign IP, high velocity card testing, chargeback risk, and account age under 1 day.",
        "high",
        "Bank account or transaction fraud",
    ),
    (
        "Review manipulation",
        "Seller offers coupon refund for bulk five star review and verified purchase review exchange to raise listing rating.",
        "medium",
        "Review or deceptive-content fraud",
    ),
    (
        "Screenshot fallback",
        "",
        "medium",
        "Fake bank alert / payment scam",
    ),
]

LEGITIMATE_CASES = [
    (
        "Legitimate bank notice",
        "Dear customer, your debit card will expire soon. Please visit any branch or use the official mobile app downloaded from your phone's app store to request a replacement. We will never ask for your PIN, OTP, password, or BVN by SMS.",
    )
]

ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def main() -> int:
    failures: list[str] = []
    for name, text, minimum_risk, scam_type in CASES:
        if name == "Screenshot fallback":
            inputs = [{"type": "image", "name": "fake-alert.png", "content": "base64", "mimeType": "image/png"}]
        elif name == "Audio fallback":
            inputs = [{"type": "audio", "name": "voice-note.wav", "content": "base64", "mimeType": "audio/wav"}]
        else:
            inputs = [{"type": "text", "name": name, "content": text}]
        verdict = server.local_verdict(inputs)
        risk = verdict["riskScore"]
        if ORDER[risk] < ORDER[minimum_risk]:
            failures.append(f"{name}: expected at least {minimum_risk}, got {risk}")
        if verdict["scamType"] != scam_type:
            failures.append(f"{name}: expected {scam_type!r}, got {verdict['scamType']!r}")
        if name not in {"Screenshot fallback", "Audio fallback"} and not verdict["isScam"]:
            failures.append(f"{name}: expected isScam=true")

    for name, text in LEGITIMATE_CASES:
        verdict = server.local_verdict([{"type": "text", "name": name, "content": text}])
        if ORDER[verdict["riskScore"]] > ORDER["medium"]:
            failures.append(f"{name}: expected no worse than medium, got {verdict['riskScore']}")

    if failures:
        print("Rules regression failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Rules regression passed: {len(CASES)} scam families and {len(LEGITIMATE_CASES)} legitimate sample covered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
