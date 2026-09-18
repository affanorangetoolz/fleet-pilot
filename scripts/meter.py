#!/usr/bin/env python3
"""meter.py — append a billable event to the current job's ledger.

Every bot that consumes a metered resource MUST call this. No silent spend.

Usage:
    python3 scripts/meter.py <kind> <qty> [--unit U] [--meta k=v ...]

Kinds (must match a resolver in run_ledger.py):
    actions_run        qty = GitHub Actions run id   (timing fetched via gh)
    fly_build          qty = builder seconds
    fly_machine        qty = machine seconds         --meta size=shared_cpu_1x_256mb
    fly_egress         qty = GB                      --meta region=na
    r2_class_a         qty = operations
    r2_class_b         qty = operations
    api_call           qty = calls                   --meta provider=serp_search
    anthropic_api      qty = tokens                  --meta model=claude-sonnet-5 kind=in|out|cache_read|cache_write batch=1
    overflow_agent     qty = credits/ACUs            --meta provider=codex
    manual             qty = USD                     --meta why="..."   (escape hatch; always disclosed)

Env:
    FLEET_JOB_ID   required — the job/issue slug, e.g. "issue-42"
    FLEET_ROOT     optional — defaults to repo root (git rev-parse --show-toplevel)
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def repo_root() -> Path:
    env = os.environ.get("FLEET_ROOT")
    if env:
        return Path(env)
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return Path(out)
    except Exception:
        return Path.cwd()


def ledger_path(job_id: str) -> Path:
    p = repo_root() / ".fleet" / "ledger"
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{job_id}.jsonl"


def parse_meta(argv: list[str]) -> dict:
    meta: dict[str, str] = {}
    i = 0
    while i < len(argv):
        if argv[i] == "--meta":
            i += 1
            while i < len(argv) and not argv[i].startswith("--"):
                if "=" in argv[i]:
                    k, v = argv[i].split("=", 1)
                    meta[k] = v
                i += 1
        elif argv[i] == "--unit":
            meta["unit"] = argv[i + 1]
            i += 2
        else:
            i += 1
    return meta


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2

    job_id = os.environ.get("FLEET_JOB_ID")
    if not job_id:
        print("meter.py: FLEET_JOB_ID is not set — refusing to log an unattributed cost.",
              file=sys.stderr)
        return 1

    kind = sys.argv[1]
    try:
        qty = float(sys.argv[2])
    except ValueError:
        qty = sys.argv[2]  # actions_run passes a run id

    event = {
        "ts": time.time(),
        "kind": kind,
        "qty": qty,
        "meta": parse_meta(sys.argv[3:]),
        "bot": os.environ.get("FLEET_BOT", "unknown"),
    }

    with ledger_path(job_id).open("a") as fh:
        fh.write(json.dumps(event) + "\n")

    print(f"metered: {kind} qty={qty} job={job_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
