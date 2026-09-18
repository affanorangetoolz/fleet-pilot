#!/usr/bin/env python3
"""Stop hook — append this session's RUN LEDGER to .fleet/fleet-costs.csv.

Does nothing unless FLEET_JOB_ID is set. Passes the session's own transcript to
run_ledger.py so shadow cost is priced from this session, not a directory search.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

RUN_LEDGER = Path(__file__).resolve().parent.parent / "scripts" / "run_ledger.py"


def main() -> int:
    job_id = os.environ.get("FLEET_JOB_ID")
    if not job_id:
        return 0
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    cmd = [sys.executable, str(RUN_LEDGER), job_id, "--append-fleet"]
    if payload.get("transcript_path"):
        cmd += ["--transcript", payload["transcript_path"]]
    result = subprocess.run(cmd)
    # Exit 2 from a Stop hook tells Claude to keep going, so never pass it through.
    return 0 if result.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
