#!/usr/bin/env bash
# CI gate — fails a PR that touches governance files, so docs-only auto-merge
# can never quietly loosen a gate. Human review via CODEOWNERS is then required.
set -euo pipefail
BASE="${GITHUB_BASE_REF:-main}"
git fetch --quiet origin "$BASE" || true
CHANGED="$(git diff --name-only "origin/$BASE"...HEAD)"

PROTECTED='^(AGENTS\.md|CLAUDE\.md|CODEOWNERS|\.coderabbit\.yaml|fly\.toml|\.github/|\.claude/|hooks/|scripts/rates\.json)'

HITS="$(printf '%s\n' "$CHANGED" | grep -E "$PROTECTED" || true)"
if [ -n "$HITS" ]; then
  echo "policy-guard: PR touches governance files:"
  printf '  %s\n' $HITS
  echo "This PR is INELIGIBLE for docs-only auto-merge and requires CODEOWNERS review."
  # Not a failure by itself — it marks the PR. Branch protection + CODEOWNERS enforce the review.
  echo "governance_touch=true" >> "${GITHUB_OUTPUT:-/dev/null}"
fi

# Hard fail: an agent-authored PR must carry a test artifact link.
if [ "${PR_AUTHOR:-}" != "" ] && printf '%s' "${PR_AUTHOR}" | grep -qi 'bot\|agent'; then
  if ! printf '%s' "${PR_BODY:-}" | grep -qiE 'artifact|coverage report|test run'; then
    echo "policy-guard: agent PR has no test artifact link. 'Done' requires proof."
    exit 1
  fi
fi
echo "policy-guard: ok"
