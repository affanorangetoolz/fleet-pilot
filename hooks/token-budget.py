#!/usr/bin/env python3
"""PostToolUse hook — abort a run that blows its token budget.

The single biggest money risk in an agent fleet is a silent retry loop.
This prices the session transcript at API rates and hard-stops past the cap.

This measures the WHOLE SESSION, not one job. If several jobs run in one
Claude Code session, they share this cap.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
RATES = json.loads((HERE / "scripts" / "rates.json").read_text())
CAP = RATES["budgets"]["per_job_shadow_usd_hard"]


def session_usd(transcript: Path) -> float:
    # The transcript writes one line per content block and repeats the message's
    # usage on each, so keep one usage record per message id or we overcount.
    per_message: dict[str, tuple[str, dict]] = {}
    for n, line in enumerate(transcript.read_text(encoding="utf-8", errors="ignore").splitlines()):
        try:
            msg = json.loads(line).get("message")
        except Exception:
            continue
        if not isinstance(msg, dict) or not msg.get("usage"):
            continue
        per_message[msg.get("id") or f"line-{n}"] = (msg.get("model") or "", msg["usage"])

    prices = RATES["anthropic_api"]
    total = 0.0
    for model, u in per_message.values():
        m = prices.get(model) or prices["claude-sonnet-5"]
        total += (u.get("input_tokens", 0) / 1e6 * m["in"]
                  + u.get("output_tokens", 0) / 1e6 * m["out"]
                  + u.get("cache_read_input_tokens", 0) / 1e6 * m["in"] * m["cache_read_mult"]
                  + u.get("cache_creation_input_tokens", 0) / 1e6 * m["in"] * m["cache_write_mult"])
    return total


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        spent = session_usd(Path(payload["transcript_path"]))
    except Exception:
        return 0  # no payload, no transcript_path, or unreadable transcript
    if spent > CAP:
        print(f"BUDGET STOP: this session has consumed ~${spent:.2f} of token value "
              f"(hard cap ${CAP:.2f}). Halt, write the RUN LEDGER, and report to Affan "
              f"before continuing. Do not retry.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
