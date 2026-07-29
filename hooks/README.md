# Hooks (optional, opt-in enforcement)

The skill works without any hooks. A model reads it and runs the linters when writing outward text. That is model-triggered, not enforced.

If you want a hard checkpoint, wire the included hook. It is opt-in on purpose: a skill should not silently install a commit-blocking hook on your machine.

## precommit-slop-check.sh

Scores a `git commit -m` message with `ste-lint.py`. If the score is over a threshold (default 3.0 per 100 words), it asks for confirmation with the specific violations. Approve to commit anyway. It never hard-blocks; slop in a commit is not a security risk.

### Enable it

1. Make it executable:
   ```
   chmod +x ~/.claude/skills/slopbliterator/hooks/precommit-slop-check.sh
   ```
2. Add to `~/.claude/settings.json` (merge into existing `hooks`, do not replace):
   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Bash",
           "hooks": [
             {
               "type": "command",
               "command": "~/.claude/skills/slopbliterator/hooks/precommit-slop-check.sh",
               "if": "Bash(git commit*)",
               "timeout": 5
             }
           ]
         }
       ]
     }
   }
   ```
3. Open `/hooks` once (or restart) so Claude Code reloads the config.

### Tune it

- Threshold: set `SLOP_THRESHOLD` in your environment (default 3.0).
- Skill path: set `SLOPBLITERATOR_DIR` if you installed somewhere other than `~/.claude/skills/slopbliterator`.

### Why advisory, not blocking

A commit message is maximally reversible and slop in it harms nobody's security. The hook surfaces a score and lets you decide. If you want a harder gate, change `permissionDecision` to `deny` in the script, but a warn-and-confirm is the sane default.
