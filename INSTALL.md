# Install Slopbliterator

Each setup has two parts. `pipx` installs the linter commands on `PATH`. The Skills CLI installs the writing rules.

The current Skills CLI requires Node.js 22.20 or newer.

Use the Git source until a package release exists:

```bash
pipx install git+https://github.com/MichelKazi/slopbliterator.git
```

After a package release, this shorter command installs the same tool:

```bash
pipx install slopbliterator
```

## Harness setup

Run the `pipx` command once. Then run the command for each harness that you use.

| Harness | Rule install command | Global rule path |
|---|---|---|
| Claude Code | `npx skills add MichelKazi/slopbliterator -g -a claude-code --copy -y` | `~/.claude/skills/slopbliterator/SKILL.md` |
| Codex | `npx skills add MichelKazi/slopbliterator -g -a codex --copy -y` | `~/.agents/skills/slopbliterator/SKILL.md` |
| Gemini CLI | `npx skills add MichelKazi/slopbliterator -g -a gemini-cli --copy -y` | `~/.agents/skills/slopbliterator/SKILL.md` |
| Cursor | `npx skills add MichelKazi/slopbliterator -g -a cursor --copy -y` | `~/.agents/skills/slopbliterator/SKILL.md` |
| Windsurf | `npx skills add MichelKazi/slopbliterator -g -a windsurf --copy -y` | `~/.codeium/windsurf/skills/slopbliterator/SKILL.md` |
| GitHub Copilot | `npx skills add MichelKazi/slopbliterator -g -a github-copilot --copy -y` | `~/.agents/skills/slopbliterator/SKILL.md` |

The Skills CLI uses `~/.agents/skills/` as a shared global directory for compatible harnesses. The `--copy` option installs a real directory instead of a symlink.

The repository-root `SKILL.md` layout works with the current Skills CLI. You do not need a `skills/slopbliterator/` directory.

## Existing Claude Code clone setup

The original setup still works:

```bash
git clone https://github.com/MichelKazi/slopbliterator.git ~/.claude/skills/slopbliterator
pipx install git+https://github.com/MichelKazi/slopbliterator.git
```

The clone supplies the Claude Code skill. The `pipx` install supplies the same PATH commands used by all harnesses.

## Commands

```bash
slop-lint < draft.txt
slop-lint README.md INSTALL.md
git diff origin/main...HEAD | slop-substance --body pr.txt --markdown
slop-lint --add banned "at the end of the day"
```

`slop-lint --add` writes to `$XDG_CONFIG_HOME/slopbliterator/banned-words.json` when that variable exists.
Otherwise, it writes to `~/.config/slopbliterator/banned-words.json`.

The packaged `banned-words.json` stays read-only. The linter loads it first, then applies user entries on top.

## Project-only install

Remove `-g` from a Skills CLI command to install rules for the current project. The CLI uses the project skill directory for that harness.
