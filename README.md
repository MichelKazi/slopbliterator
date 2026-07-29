# Slopbliterator

A slop obliterator for LLMs. Review your machine-generated writing (PRs, commits, docs, error messages) with a deterministic linter BEFORE you hand it to an organic brain powered meat machine ([homo sapien](https://en.wikipedia.org/wiki/Homo_sapiens)). Respect the meat machine's time.

Slop is as much a **form** problem as it is a vocabulary one. Banning one claudism at a time is a losing game of whack-a-mole. Aircraft manuals from 1986 can teach us and LLMs how to write technical documentation that is harder to misread, which is why Slopbliterator follows [ASD-STE100 Simplified Technical English](https://asd-ste100.org).

I'm also just f***ing tired of reading "load-bearing" and "smoking gun" everywhere.

### Demo

Real technical facts (an H.264 encoder quirk), written the way an LLM would write them up. Every claim is true. **18.39** violations per 100 words, down to **0.00**.

```diff
- It's important to note that our H.264 encoding path leverages a rather nuanced,
- load-bearing workaround that is absolutely critical to ensuring optimal streaming
- performance. Specifically, we deliberately omit the `max_ref_frames` parameter — a
- subtle but powerful optimization — because VideoToolbox on Apple Silicon fundamentally
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
| banned tells | "it's important to note", "load-bearing", "going forward", "worth noting" | cut |
| marketing words | "powerful", "nuanced", "leverages", "fundamentally" | cut, or say the fact |
| em dashes | 2, stitching asides into the sentence | split into sentences |
| sentence over 20 words | two run-ons, worst 40+ words | one idea per sentence |

### Install and use

```bash
cp -r slopbliterator ~/.claude/skills/slopbliterator
```

```bash
python3 ste-lint.py < draft.txt                    # score a draft (JSON + suggested swaps)
python3 ste-lint.py pr.md notes.md                 # score files (table)
git diff origin/main...HEAD | python3 substance-lint.py --body pr.txt --markdown
python3 ste-lint.py --add banned "at the end of the day"   # teach it a new tell
```

Target under ~1.5 violations per 100 words. Baseline AI writing is ~4.4. The linters find `banned-words.json` next to themselves, so no config.

### How it works

Two layers, matched to how deterministic each is.

- **Form** (`ste-lint.py`): fully deterministic. Long sentences, semicolons, em dashes, passive voice, nominalizations, phrasal verbs, marketing words, banned tells. Slop is always wrong, so fix it.
- **Substance** (`substance-lint.py`): deterministic detection, human judgment. It can prove a PR description just narrates the diff. It cannot prove the content is worth saying. It flags, you decide.

`banned-words.json` grows as you go: each `--add` teaches the linter your preferred swaps, so the next draft is scored with the alternative pre-chosen.

### Make it yours

The base is voice-neutral on purpose. STE strips voice; you add yours back on top.

- **Voice:** drop a persona file in as `persona.md`. Want a tired engineer at 4pm Friday? `cp personas/tired-engineer.md persona.md`. Write your own by copying either example. No persona means pure neutral STE.
- **Vocabulary:** `--add` your own tells and alternatives.
- **Rules:** edit `SKILL.md`.

### Enforce it (optional)

`hooks/precommit-slop-check.sh` scores a commit message before it lands and asks for confirmation if it is sloppy. Opt-in, advisory, never a hard block. See `hooks/README.md`.

### Limits and credit

The linter fixes the form of slop. It cannot make a hollow paragraph true, and it is wrong for anything that needs a voice. STE approach and original linter from [woosal1337's "the cure for AI slop"](https://github.com/woosal1337/blog/tree/main/videos/ep01-the-cure-for-ai-slop); Slopbliterator adds the substance check, over-explanation check, editable banned-word list, and persona layer. MIT licensed.
