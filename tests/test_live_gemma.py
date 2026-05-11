"""Live test against Google-hosted Gemma to verify scam detection accuracy."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import server  # noqa: E402

server.load_local_env()

if not os.getenv("GOOGLE_API_KEY"):
    print("ERROR: GOOGLE_API_KEY not set. Cannot run live test.")
    raise SystemExit(1)

SCAM_CASES = [
    (
        "419 advance-fee",
        "I am Barrister John representing a deceased client with unclaimed fund of USD 10.5 million. "
        "You are next of kin beneficiary. This is strictly confidential. Send processing fee to release the funds urgently.",
    ),
    (
        "SMS phishing",
        "Your bank account has been suspended. Verify your BVN and OTP now at http://bad.example to restore access.",
    ),
    (
        "Fake job fee",
        "Good afternoon. Chevron shortlisted you for a job. Pay registration fee before Friday ASAP.",
    ),
    (
        "Crypto doubling",
        "Double your bitcoin in 48 hours. Guaranteed profit. Send NGN 50000 activation payment on WhatsApp.",
    ),
    (
        "Romance emergency",
        "I love you and want to be with you, but I am stranded at customs after peacekeeping travel. "
        "Please send money urgently by gift card so I can leave the hospital and come home.",
    ),
    (
        "Invoice payment change",
        "Please process this vendor invoice today. Our bank details have changed, so make urgent payment by wire transfer to the new account number below.",
    ),
]

LEGIT_CASES = [
    (
        "Legitimate bank notice",
        "Dear customer, your debit card will expire soon. Please visit any branch or use the official mobile app "
        "downloaded from your phone's app store to request a replacement. We will never ask for your PIN, OTP, password, or BVN by SMS.",
    ),
]


def run_one(name: str, text: str) -> dict:
    inputs = [{"type": "text", "name": name, "content": text}]
    raw = server.call_google_gemma(inputs)
    return server.parse_verdict(raw)


def main() -> int:
    failures: list[str] = []
    print(f"{'='*70}")
    print(f"LIVE GEMMA TEST — {len(SCAM_CASES)} scam + {len(LEGIT_CASES)} legit cases")
    print(f"Model: {os.getenv('GOOGLE_MODEL', 'gemma-4-26b-a4b-it')}")
    print(f"{'='*70}\n")

    for name, text in SCAM_CASES:
        print(f"  Testing: {name}...", end=" ", flush=True)
        start = time.time()
        try:
            v = run_one(name, text)
            ms = int((time.time() - start) * 1000)
            is_scam = v.get("isScam", False)
            risk = v.get("riskScore", "?")
            pct = v.get("riskPercentage", "?")
            scam_type = v.get("scamType", "?")

            status = "PASS" if is_scam else "FAIL"
            if not is_scam:
                failures.append(f"{name}: isScam=false, risk={risk}, pct={pct}")

            print(f"[{status}] isScam={is_scam}, risk={risk}, pct={pct}%, type={scam_type} ({ms}ms)")
        except Exception as e:
            failures.append(f"{name}: EXCEPTION {e}")
            print(f"[ERROR] {e}")
        time.sleep(1)

    print()
    for name, text in LEGIT_CASES:
        print(f"  Testing: {name}...", end=" ", flush=True)
        start = time.time()
        try:
            v = run_one(name, text)
            ms = int((time.time() - start) * 1000)
            is_scam = v.get("isScam", False)
            risk = v.get("riskScore", "?")
            pct = v.get("riskPercentage", "?")

            status = "PASS" if not is_scam and risk == "low" else "FAIL"
            if is_scam or risk not in {"low", "medium"}:
                failures.append(f"{name}: false positive — isScam={is_scam}, risk={risk}")

            print(f"[{status}] isScam={is_scam}, risk={risk}, pct={pct}% ({ms}ms)")
        except Exception as e:
            failures.append(f"{name}: EXCEPTION {e}")
            print(f"[ERROR] {e}")

    print(f"\n{'='*70}")
    if failures:
        print(f"RESULT: {len(failures)} FAILURE(S)")
        for f in failures:
            print(f"  - {f}")
        return 1
    else:
        print(f"RESULT: ALL {len(SCAM_CASES) + len(LEGIT_CASES)} CASES PASSED")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
