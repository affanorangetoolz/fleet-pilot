#!/usr/bin/env bash
# PreToolUse hook — hard-blocks agent writes to self-governing files.
# An agent that can edit its own rules has no rules.
# Exit 2 = deny the tool call and tell the model why.
# Fails closed: exit 0 only when the payload parsed AND the path is not protected.
set -euo pipefail
payload="$(cat)"
# Prints tool_input.file_path; exits non-zero on bad JSON, a missing tool_input,
# or a missing/empty/non-string file_path. A python3 failure also lands here.
if ! target="$(printf '%s' "$payload" | python3 -c '
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
path = json.load(sys.stdin)["tool_input"]["file_path"]
if not isinstance(path, str) or not path.strip():
    raise SystemExit(1)
print(path)
' 2>/dev/null)"; then
  echo "BLOCKED: the path guard could not read its input (not JSON, or no usable tool_input.file_path). Failing closed; the edit was not allowed." >&2
  exit 2
fi
target="$(printf '%s' "$target" | tr '\\' '/')"

PROTECTED='(^|/)(AGENTS\.md|CLAUDE\.md|\.coderabbit\.yaml|fly\.toml|CODEOWNERS)$|(^|/)\.github/|(^|/)\.claude/|(^|/)hooks/|(^|/)scripts/(rates\.json|policy-guard\.sh|run_ledger\.py|meter\.py)$'

if printf '%s' "$target" | grep -Eq "$PROTECTED"; then
  echo "BLOCKED: $target is a governance file. Agents may not edit gates, rates, CI, or their own instructions. Propose the change in your report; the human merge desk applies it via a CODEOWNERS-reviewed PR." >&2
  exit 2
fi
exit 0
