#!/usr/bin/env bash
# OPT-IN Claude Code hook: score the commit message for slop before it lands.
#
# This is NOT wired by default. To enable, add it to your settings.json as a
# PreToolUse hook on Bash with `if: "Bash(git commit*)"` (see hooks/README.md).
#
# It extracts the commit message from the `git commit -m` command, scores it with
# ste-lint.py, and if the score is over the threshold it asks for confirmation
# (permissionDecision "ask") with the specific violations. Approve to commit anyway.
# Advisory by design: it never hard-blocks. Slop in a commit is not a security risk.
#
# Threshold and skill path are configurable below.

set -euo pipefail

THRESHOLD="${SLOP_THRESHOLD:-3.0}"                       # violations per 100 words
SKILL_DIR="${SLOPBLITERATOR_DIR:-$HOME/.claude/skills/slopbliterator}"
LINT="$SKILL_DIR/ste-lint.py"

payload="$(cat 2>/dev/null || true)"
[ -x "$(command -v jq)" ] || exit 0
[ -f "$LINT" ] || exit 0

cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
case "$cmd" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

# Pull the -m message (single or double quoted). Best-effort; skip if none found.
msg="$(printf '%s' "$cmd" | sed -nE "s/.*-m[[:space:]]+\"([^\"]*)\".*/\1/p; s/.*-m[[:space:]]+'([^']*)'.*/\1/p" | head -1)"
[ -z "$msg" ] && exit 0

score="$(printf '%s' "$msg" | python3 "$LINT" 2>/dev/null | jq -r '.total_per100w // 0' 2>/dev/null || echo 0)"

# bash float compare via awk
over="$(awk -v s="$score" -v t="$THRESHOLD" 'BEGIN{print (s+0 > t+0) ? 1 : 0}')"
[ "$over" = "1" ] || exit 0

viol="$(printf '%s' "$msg" | python3 "$LINT" 2>/dev/null | jq -rc '[.violations | to_entries[] | select(.value>0) | .key] | join(", ")' 2>/dev/null || echo "")"

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": "Slop check: commit message scores ${score}/100w (threshold ${THRESHOLD}). Flagged: ${viol}. Run it through the slopbliterator skill, or approve to commit as is."
  }
}
EOF
