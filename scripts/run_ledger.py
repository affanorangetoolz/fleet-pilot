#!/usr/bin/env python3
"""run_ledger.py — turn a job's metered events into the RUN LEDGER block.

Two separate ledgers, never mixed:

  CASH    real money billed by a vendor because this job ran.
          Excludes anything already covered by a subscription you pay anyway.
  SHADOW  token value consumed inside a subscription. $0 cash. Tracked so you
          can see burn rate and catch runaway agents before they eat the plan.

Usage:
    python3 scripts/run_ledger.py <job-id> [--json] [--append-fleet] [--transcript PATH]

Requires: python3 stdlib only. `gh` CLI optional (for Actions timing).
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RATES = json.loads((HERE / "rates.json").read_text())


def repo_root() -> Path:
    env = os.environ.get("FLEET_ROOT")
    if env:
        return Path(env)
    try:
        return Path(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                   capture_output=True, text=True, check=True).stdout.strip())
    except Exception:
        return Path.cwd()


def load_events(job_id: str) -> list[dict]:
    p = repo_root() / ".fleet" / "ledger" / f"{job_id}.jsonl"
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


# ---------------------------------------------------------------- resolvers

def actions_timing(run_id: str) -> dict:
    """Billable ms per OS from the GitHub API. Returns {} if gh is unavailable."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    try:
        args = ["gh", "api", f"repos/{repo}/actions/runs/{run_id}/timing"] if repo else \
               ["gh", "api", f"repos/{{owner}}/{{repo}}/actions/runs/{run_id}/timing"]
        out = subprocess.run(args, capture_output=True, text=True, check=True).stdout
        return json.loads(out).get("billable", {})
    except Exception:
        return {}


def cost_actions(ev: dict) -> tuple[float, str]:
    billable = actions_timing(str(ev["qty"]))
    if not billable:
        return 0.0, "run %s (timing unavailable — verify manually)" % ev["qty"]
    rates = RATES["github_actions"]
    total, parts = 0.0, []
    for os_name, data in billable.items():
        minutes = data.get("total_ms", 0) / 60000.0
        key = {"UBUNTU": "ubuntu_per_min", "WINDOWS": "windows_per_min",
               "MACOS": "macos_per_min"}.get(os_name.upper())
        if not key:
            continue
        total += minutes * rates[key]
        parts.append(f"{minutes:.1f} {os_name.title()}-min")
    return total, ", ".join(parts)


def cost_fly_build(ev):
    return float(ev["qty"]) * RATES["fly_io"]["builder_per_sec"], f"{ev['qty']:.0f} builder-s"


def cost_fly_machine(ev):
    size = ev["meta"].get("size", "shared_cpu_1x_256mb")
    rate = RATES["fly_io"].get(f"{size}_per_sec", RATES["fly_io"]["shared_cpu_1x_256mb_per_sec"])
    return float(ev["qty"]) * rate, f"{ev['qty']:.0f} machine-s ({size})"


def cost_fly_egress(ev):
    region = ev["meta"].get("region", "na")
    key = "egress_apac_per_gb" if region == "apac" else "egress_na_eu_per_gb"
    return float(ev["qty"]) * RATES["fly_io"][key], f"{ev['qty']:.3f} GB ({region})"


def cost_r2_a(ev):
    return float(ev["qty"]) / 1e6 * RATES["cloudflare_r2"]["class_a_per_million_ops"], \
        f"{ev['qty']:.0f} class-A ops"


def cost_r2_b(ev):
    return float(ev["qty"]) / 1e6 * RATES["cloudflare_r2"]["class_b_per_million_ops"], \
        f"{ev['qty']:.0f} class-B ops"


def cost_api_call(ev):
    provider = ev["meta"].get("provider", "unknown")
    rate = RATES["external_apis"].get(provider, 0.0)
    return float(ev["qty"]) * rate, f"{ev['qty']:.0f} calls ({provider})"


def cost_anthropic_api(ev):
    """CASH — only for jobs billed to an API key, never subscription work."""
    model = ev["meta"].get("model", "claude-sonnet-5")
    tok_kind = ev["meta"].get("kind", "in")
    m = RATES["anthropic_api"].get(model)
    if not m:
        return 0.0, f"{ev['qty']:.0f} tok (unknown model {model})"
    base = m["in"] if tok_kind in ("in", "cache_read", "cache_write") else m["out"]
    mult = {"cache_read": m["cache_read_mult"], "cache_write": m["cache_write_mult"]}.get(tok_kind, 1.0)
    usd = float(ev["qty"]) / 1e6 * base * mult
    if ev["meta"].get("batch") == "1":
        usd *= RATES["anthropic_api"]["batch_discount"]
    return usd, f"{ev['qty']/1000:.0f}k {tok_kind} ({model})"


def cost_overflow(ev):
    provider = ev["meta"].get("provider", "codex")
    rate = RATES["overflow_agents"].get(f"{provider}_credit_usd") \
        or RATES["overflow_agents"].get(f"{provider}_acu_usd", 0.0)
    return float(ev["qty"]) * rate, f"{ev['qty']:.0f} units ({provider})"


def cost_manual(ev):
    return float(ev["qty"]), ev["meta"].get("why", "manual entry")


RESOLVERS = {
    "actions_run": ("GitHub Actions", cost_actions),
    "fly_build": ("Fly.io build", cost_fly_build),
    "fly_machine": ("Fly.io machines", cost_fly_machine),
    "fly_egress": ("Fly.io egress", cost_fly_egress),
    "r2_class_a": ("R2 write ops", cost_r2_a),
    "r2_class_b": ("R2 read ops", cost_r2_b),
    "api_call": ("External APIs", cost_api_call),
    "anthropic_api": ("Anthropic API", cost_anthropic_api),
    "overflow_agent": ("Overflow agent", cost_overflow),
    "manual": ("Manual", cost_manual),
}


# ------------------------------------------------------------- shadow cost

def usage_by_message(f: Path) -> dict:
    """{message id: (model, usage)} for one transcript.

    The transcript writes one line per content block and repeats the message's
    usage on each, so keep one usage record per message id or we overcount.
    """
    out = {}
    for n, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines()):
        try:
            rec = json.loads(line)
        except Exception:
            continue
        msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
        usage = msg.get("usage") or rec.get("usage")
        if not usage:
            continue
        model = msg.get("model") or rec.get("model") or "claude-sonnet-5"
        out[msg.get("id") or f"{f.name}:{n}"] = (model, usage)
    return out


def shadow_from_transcript(job_id: str, transcript: Path | None = None) -> dict:
    """Read Claude Code session JSONL and total token usage per model.

    Subscription work costs no cash. We price it anyway at published API rates
    so runaway loops are visible before they exhaust the plan.

    With `transcript`, read exactly that file. Otherwise search every session
    under ~/.claude/projects that mentions the job id.
    """
    if transcript is not None:
        files = [transcript] if transcript.exists() else []
    else:
        base = Path.home() / ".claude" / "projects"
        files = []
        for f in base.rglob("*.jsonl") if base.exists() else []:
            try:
                if job_id in f.name:
                    files.append(f)
                    continue
                with f.open(encoding="utf-8", errors="ignore") as fh:
                    if job_id in fh.read(4000):  # head only; transcripts can be huge
                        files.append(f)
            except Exception:
                continue
    totals: dict[str, dict[str, int]] = {}
    for f in files:
        try:
            records = usage_by_message(f)
        except Exception:
            continue
        for model, usage in records.values():
            t = totals.setdefault(model, {"in": 0, "out": 0, "cache_read": 0, "cache_write": 0})
            t["in"] += usage.get("input_tokens", 0)
            t["out"] += usage.get("output_tokens", 0)
            t["cache_read"] += usage.get("cache_read_input_tokens", 0)
            t["cache_write"] += usage.get("cache_creation_input_tokens", 0)
    return totals


def price_shadow(totals: dict) -> tuple[float, list[str]]:
    lines, grand = [], 0.0
    for model, t in totals.items():
        key = model if model in RATES["anthropic_api"] else "claude-sonnet-5"
        m = RATES["anthropic_api"][key]
        usd = (t["in"] / 1e6 * m["in"]
               + t["out"] / 1e6 * m["out"]
               + t["cache_read"] / 1e6 * m["in"] * m["cache_read_mult"]
               + t["cache_write"] / 1e6 * m["in"] * m["cache_write_mult"])
        grand += usd
        lines.append(f"  {key:<20} {t['in']/1000:.0f}k in / {t['out']/1000:.0f}k out / "
                     f"{t['cache_read']/1000:.0f}k cache-read  ~${usd:.2f} equiv")
    return grand, lines


# ------------------------------------------------------------------- render

def main() -> int:
    # The ledger box uses non-ASCII rules; Windows encodes piped stdout as cp1252.
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("job_id")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--append-fleet", action="store_true")
    ap.add_argument("--transcript", type=Path, metavar="PATH",
                    help="price this session transcript instead of searching ~/.claude/projects")
    args = ap.parse_args()

    events = load_events(args.job_id)
    buckets: dict[str, list] = {}
    cash_total = 0.0

    for ev in events:
        label, fn = RESOLVERS.get(ev["kind"], (None, None))
        if not fn:
            continue
        try:
            usd, detail = fn(ev)
        except Exception as exc:
            usd, detail = 0.0, f"unresolved ({exc})"
        cash_total += usd
        buckets.setdefault(label, []).append((detail, usd))

    shadow_totals = shadow_from_transcript(args.job_id, args.transcript)
    shadow_usd, shadow_lines = price_shadow(shadow_totals)

    b = RATES["budgets"]
    flags = []
    if cash_total > b["per_job_cash_usd_hard"]:
        flags.append(f"CASH OVER HARD CAP (${b['per_job_cash_usd_hard']:.2f}) — STOP, escalate to Affan")
    elif cash_total > b["per_job_cash_usd_soft"]:
        flags.append(f"cash over soft cap (${b['per_job_cash_usd_soft']:.2f}) — explain why")
    if shadow_usd > b["per_job_shadow_usd_hard"]:
        flags.append(f"SHADOW OVER HARD CAP (${b['per_job_shadow_usd_hard']:.2f}) — likely agent loop")
    elif shadow_usd > b["per_job_shadow_usd_soft"]:
        flags.append(f"shadow over soft cap (${b['per_job_shadow_usd_soft']:.2f})")

    if args.json:
        print(json.dumps({"job": args.job_id, "cash_usd": round(cash_total, 4),
                          "shadow_usd": round(shadow_usd, 2), "flags": flags,
                          "buckets": {k: [(d, round(u, 4)) for d, u in v]
                                      for k, v in buckets.items()}}, indent=2))
        return 0

    w = 62
    print("\n" + "─" * w)
    print(f" RUN LEDGER · {args.job_id} · {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")
    print("─" * w)
    print(" CASH BILLED BY THIS RUN  (excludes subscriptions already paid)")
    if not buckets:
        print("   none metered")
    for label, rows in buckets.items():
        for detail, usd in rows:
            print(f"   {label:<18} {detail:<26} ${usd:>8.4f}")
    print("   " + "-" * (w - 5))
    print(f"   {'TOTAL CASH':<46} ${cash_total:>8.4f}")
    print()
    print(" SUBSCRIPTION-COVERED  ($0 cash — burn tracking only)")
    if shadow_lines:
        for line in shadow_lines:
            print(line)
        print(f"   {'~equivalent if metered':<46} ${shadow_usd:>8.2f}")
    else:
        print("   no transcript usage found for this job")
    if flags:
        print()
        for f in flags:
            print(f"  !! {f}")
    print("─" * w + "\n")

    if args.append_fleet:
        csv = repo_root() / ".fleet" / "fleet-costs.csv"
        csv.parent.mkdir(parents=True, exist_ok=True)
        new = not csv.exists()
        with csv.open("a") as fh:
            if new:
                fh.write("date,repo,job,cash_usd,shadow_usd\n")
            fh.write(f"{datetime.now(timezone.utc):%Y-%m-%d},"
                     f"{os.environ.get('GITHUB_REPOSITORY', repo_root().name)},"
                     f"{args.job_id},{cash_total:.4f},{shadow_usd:.2f}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
