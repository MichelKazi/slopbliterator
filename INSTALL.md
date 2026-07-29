# Install Slopbliterator

The installer detects supported coding harnesses. It installs the linter commands with `pipx`, then installs the writing skill for each detected harness. It pins Skills CLI 1.4.9 so the Node.js requirement stays stable.

It requires Node.js 18 or newer and `pipx` on `PATH`.

On macOS or Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/MichelKazi/slopbliterator/main/install.sh | sh
```

On Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/MichelKazi/slopbliterator/main/install.ps1 | iex
```

The installer checks for Claude Code, Codex, Gemini CLI, Cursor, Windsurf, and GitHub Copilot. Use `--list` to see what it found. Use `--only codex` to select one harness, or `--all` to select all six.

Pass options to the shell script after `sh -s --`. You can also use the Node entry point:

```bash
curl -fsSL https://raw.githubusercontent.com/MichelKazi/slopbliterator/main/install.sh | sh -s -- --only codex --with-init
npx -y github:MichelKazi/slopbliterator --dry-run --all
```

`--with-init` adds an always-on rule to the current project. The installer preserves existing root instruction files. It owns only its marked block and its named rule files.

## Install targets

| Harness | Detection | Global skill path | Project rule from `--with-init` |
|---|---|---|---|
| Claude Code | `claude` command | `~/.claude/skills/slopbliterator/SKILL.md` | `CLAUDE.md` |
| Codex | `codex` command | `~/.agents/skills/slopbliterator/SKILL.md` | `AGENTS.md` |
| Gemini CLI | `gemini` command | `~/.agents/skills/slopbliterator/SKILL.md` | `GEMINI.md` |
| Cursor | command or macOS app | `~/.agents/skills/slopbliterator/SKILL.md` | `.cursor/rules/slopbliterator.mdc` |
| Windsurf | command or macOS app | `~/.codeium/windsurf/skills/slopbliterator/SKILL.md` | `.windsurf/rules/slopbliterator.md` |
| GitHub Copilot | command or editor extension | `~/.agents/skills/slopbliterator/SKILL.md` | `.github/instructions/slopbliterator.instructions.md` |

The Skills CLI uses `~/.agents/skills/` as a shared global directory for compatible harnesses. The `--copy` option installs a real directory instead of a symlink.

The repository-root `SKILL.md` layout works with the current Skills CLI. A `skills/slopbliterator/` directory is not required.

## Installer options

```text
--list              Show harness detection and exit
--only <harness>    Install one harness. Repeat for more harnesses
--all               Install all six supported harnesses
--with-init         Add always-on rules to the current project
--force             Replace the linter install and owned rule files
--dry-run           Print actions without changing files
--uninstall         Remove selected installs and project rules
```

Run the local installer from a clone with `./install.sh`. Run `node bin/install.js --help` for the same options.

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

## Manual skill install

The installer uses this command shape for each selected harness:

```bash
npx skills@1.4.9 add MichelKazi/slopbliterator --skill slopbliterator -g -a codex --copy -y
```

Remove `-g` for a project-only skill install. The Skills CLI uses the project skill directory for that harness.
