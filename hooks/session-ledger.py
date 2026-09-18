#!/usr/bin/env python3
"""Stop hook — append this session's RUN LEDGER to .fleet/fleet-costs.csv.

Does nothing unless FLEET_JOB_ID is set. Passes the session's own transcript to
run_ledger.py so shadow cost is priced from this session, not a directory search.

Fails open: if run_ledger.py or the rates table can't be found, it skips the
ledger and exits 0. A meter that can't find itself must not block work.
FLEET_HOOKS_OFF=1 turns it off entirely.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

# settings.json runs this by absolute path under the main checkout's root,
# so these resolve there even when the session is inside a linked worktree.
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
RUN_LEDGER = SCRIPTS / "run_ledger.py"
RATES_FILE = SCRIPTS / "rates.json"


def main() -> int:
    if os.environ.get("FLEET_HOOKS_OFF") == "1":
        return 0
    job_id = os.environ.get("FLEET_JOB_ID")
    if not job_id:
        return 0
    if not (RUN_LEDGER.is_file() and RATES_FILE.is_file()):
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
