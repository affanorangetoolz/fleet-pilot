#!/usr/bin/env bash
# PreToolUse hook — hard-blocks agent writes to self-governing files.
# An agent that can edit its own rules has no rules.
# Exit 2 = deny the tool call and tell the model why.
# Fails closed: exit 0 only when the payload parsed AND the path is not protected.
# Deliberately ignores FLEET_HOOKS_OFF: a guard an env var can switch off is not a guard.
set -euo pipefail
payload="$(cat)"
# Prints tool_input.file_path with forward slashes. A path under .claude/worktrees/<name>/
# is printed relative to that worktree: a linked worktree is a full checkout, so its files
# are judged as if at the repo root (otherwise every worktree edit matches .claude/).
# Exit 1: bad JSON, missing tool_input, or missing/empty/non-string file_path.
# Exit 3: a ".." segment, which could climb out of a worktree after the prefix is stripped.
# A python3 failure also lands in the catch-all below.
rc=0
target="$(printf '%s' "$payload" | python3 -c '
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
path = json.load(sys.stdin)["tool_input"]["file_path"]
if not isinstance(path, str) or not path.strip():
    raise SystemExit(1)
path = path.replace("\\", "/")
if ".." in path.split("/"):
    raise SystemExit(3)
print(re.sub(r"^(?:.*?/)?\.claude/worktrees/[^/]+/", "", path, count=1))
' 2>/dev/null)" || rc=$?
if [ "$rc" -eq 3 ]; then
  echo "BLOCKED: the target path contains a '..' segment. Use a normalized absolute path; the edit was not allowed." >&2
  exit 2
elif [ "$rc" -ne 0 ]; then
  echo "BLOCKED: the path guard could not read its input (not JSON, or no usable tool_input.file_path). Failing closed; the edit was not allowed." >&2
  exit 2
fi

PROTECTED='(^|/)(AGENTS\.md|CLAUDE\.md|\.coderabbit\.yaml|fly\.toml|CODEOWNERS)$|(^|/)\.github/|(^|/)\.claude/|(^|/)hooks/|(^|/)scripts/(rates\.json|policy-guard\.sh|run_ledger\.py|meter\.py)$'

if printf '%s' "$target" | grep -Eq "$PROTECTED"; then
  echo "BLOCKED: $target is a governance file. Agents may not edit gates, rates, CI, or their own instructions. Propose the change in your report; the human merge desk applies it via a CODEOWNERS-reviewed PR." >&2
  exit 2
fi
exit 0
