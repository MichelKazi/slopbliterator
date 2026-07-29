# Slopbliterator

A slop obliterator for LLMs. Review your machine-generated writing (PRs, commits, docs, error messages) with a deterministic linter BEFORE you hand it to an organic brain powered [meat machine](https://en.wikipedia.org/wiki/Homo_sapiens). Respect the [meat machine](https://en.wikipedia.org/wiki/Homo_sapiens)'s time.

Slop is as much a **form** problem as it is a vocabulary one. Banning one claudism at a time is a losing game of whack-a-mole. Aircraft manuals from 1986 can teach us and LLMs how to write technical documentation that is harder to misread, which is why Slopbliterator follows [ASD-STE100 Simplified Technical English](https://asd-ste100.org).

I'm also just f***ing tired of reading "load-bearing" and "smoking gun" everywhere.

<img width="650" height="362" alt="perfect-blue-sky-background--with-fluffy-clouds(1)" src="https://github.com/user-attachments/assets/8cdf8c7f-a401-4700-aba2-72e09c196379" />

### Two checks for code-review prose

Slopbliterator runs locally and uses no runtime dependencies. It checks the form of technical prose and whether a PR description adds information beyond the diff.

- **Form**: `slop-lint` checks sentence length, punctuation, voice, weak verbs, stock phrases, and marketing language.

- **Substance**: `slop-substance` checks diff narration, repeated Result sections, reviewer instructions, missing context, and bare code symbols.

The form checker began with Ege Çelebi's open-source STE linter. This repository adds the substance checker, multi-harness installation, persistent user vocabulary, and precision-focused detector tests.

### A real H.264 example

These technical facts describe an H.264 encoder quirk. The first version scores **20.51** violations per 100 words. The second scores **0.00**.

```diff
- It's important to note that our H.264 encoding path leverages a rather nuanced,
- load-bearing workaround that is absolutely critical to ensuring optimal streaming
- performance. Specifically, we deliberately omit the `max_ref_frames` parameter, a
- subtle but powerful optimization, because VideoToolbox on Apple Silicon fundamentally
- produces all-IDR output when `ReferenceBufferCount` is set to 1, which in turn inflates
- bandwidth by roughly 3x and introduces frame drops. It's worth noting that HEVC and AV1
- remain completely unaffected. Going forward, H.264 also leverages `-low_delay`.
+ The H.264 path omits `max_ref_frames` on purpose. VideoToolbox on Apple Silicon
+ produces all-IDR output when `ReferenceBufferCount` is 1. That inflates bandwidth about
+ 3x and drops frames. HEVC and AV1 do not have this quirk. H.264 also sets `-low_delay`
+ to cut latency.
```

| Detected by | Found | Fixed |
|---|---|---|
| banned tells | ten hits, including `load-bearing`, `going forward`, and `worth noting` | cut |
| marketing words | `powerful` | cut, or state the fact |
| grammar | two contractions and one passive hit | expand or name the actor |
| long sentences | two run-ons, worst 37 words | one idea per sentence |

### Install

The installer detects Claude Code, Codex, Gemini CLI, Cursor, Windsurf, and Copilot. It installs the PATH commands and the matching writing skill. See [INSTALL.md](INSTALL.md) for options and manual setup.

```bash
curl -fsSL https://raw.githubusercontent.com/MichelKazi/slopbliterator/main/install.sh | sh
```

### Use

Check text from standard input or files:

```bash
slop-lint < draft.txt
slop-lint pr.md notes.md
```

Check whether a PR description narrates its diff:

```bash
git diff origin/main...HEAD | slop-substance --body pr.txt --markdown
```

Add a personal term and its replacement:

```bash
slop-lint --add banned "at the end of the day" "state the fact"
```

User terms live outside the installed package, so updates do not overwrite them.

### Detection quality

The repository contains 95 labeled cases. Each detector gets known-slop cases that must fire and known-clean cases that must remain quiet.

```bash
python3 corpus/score.py --baseline corpus/baseline.json
```

The harness reports precision, recall, false positives, false negatives, and baseline deltas for each detector. The corpus is small, so its scores are regression evidence rather than population estimates.

Precision comes first. A noisy prose checker gets muted.

The Issue 9 coverage model includes all 53 numbered STE rules. The model classifies each rule as enforced, advisory, or manual. The classification prevents contextual rules from becoming noisy regex violations.

```bash
slop-lint --coverage
slop-lint --mode procedure < steps.txt
slop-lint --mode descriptive < reference.txt
```

The default STE-flavored mode keeps the original score contract for general coding prose. Procedure mode uses a 20-word limit. Descriptive mode uses a 25-word limit.

### Make it yours

The packaged word list stays read-only. Use `--add` for personal terms and replacements.

The writing skill uses a neutral voice by default. Copy a file from `personas/` to `persona.md` when documentation needs a specific voice.

Edit `SKILL.md` when you want to change the writing rules themselves.

### Add it to a repository

`hooks/precommit-slop-check.sh` checks a commit message before it lands. The hook is optional and advisory. See `hooks/README.md`.

The linter also works in scripts and CI because `slop-lint` returns JSON for standard input. File mode prints one summary line per file.

### Limits

The form linter cannot prove that prose is true or useful. The substance linter reports possible problems, not verdicts.

Slopbliterator does not automatically enforce every ASD-STE100 rule. It does not include the copyrighted controlled dictionary. Do not use it as a certified STE checker.

Do not run strict technical-writing rules over marketing copy or other text that needs a distinct voice.

### Credit and license

Skills that remove AI slop may now qualify as AI slop themselves. Slopbliterator did not invent this category. It is another plugin to plug in. Its useful difference is the measured, diff-aware review gate described above.

The original STE skill and linter come from Ege Çelebi's MIT-licensed ["The cure for AI slop" kit](https://github.com/woosal1337/blog/tree/main/videos/ep01-the-cure-for-ai-slop). Slopbliterator preserves the [upstream license](LICENSE-upstream).

Related STE tools:

- [ste](https://github.com/cstaszak/ste)

- [claude-ste](https://github.com/thought-stuff/claude-ste)

- [asd-ste100-checker](https://github.com/sourdough-bread/asd-ste100-checker)

- [SimpleEnglish](https://github.com/AminBlg/SimpleEnglish)

- [slop-lint](https://github.com/tylerriccio33/slop-lint)

- [ste100-vale-rules](https://github.com/aldair-torres/ste100-vale-rules)

Related anti-slop tools and skills:

- [no-slop](https://github.com/Byk3y/no-slop)

- [vale-ai-tells](https://github.com/tbhb/vale-ai-tells)

- [deslop](https://github.com/adamcharnock/deslop)

- [slop-cop](https://github.com/MahmoudHalat/slop-cop)

- [SlopScore](https://github.com/jman4162/slopscore)

- [humanize-ai-writing](https://github.com/haidrrrry/humanize-ai-writing)

- [untell](https://github.com/ssamba1/untell)

- [no-ai-slop](https://github.com/petergyang/no-ai-slop)

- [humanizer](https://github.com/blader/humanizer)

- [humanize](https://github.com/kimhons/humanize)

Slopbliterator is an unofficial tool. ASD and the Simplified Technical English Maintenance Group do not endorse or certify it. The full ASD-STE100 standard remains copyrighted and is available from [asd-ste100.org](https://asd-ste100.org).
