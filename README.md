# Slopbliterator

A slop obliterator for LLMs. Check machine-written prose before you hand it to an organic brain powered meat machine. Respect the meat machine's time.

Slop is a form problem and a vocabulary problem. A word blacklist cannot fix it alone. Slopbliterator uses [ASD-STE100 Simplified Technical English](https://asd-ste100.org) to make technical prose harder to misread.

I am also tired of reading `load-bearing` and `smoking gun` everywhere.

<img width="650" height="362" alt="perfect-blue-sky-background--with-fluffy-clouds(1)" src="https://github.com/user-attachments/assets/8cdf8c7f-a401-4700-aba2-72e09c196379" />

### Real Examples from a Real AI Slop Machine

These technical facts describe an H.264 encoder quirk. The first version scores **18.39** violations per 100 words. The second scores **0.00**.

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
| banned tells | `it's important to note`, `load-bearing`, `going forward`, `worth noting` | cut |
| marketing words | `powerful`, `nuanced`, `leverages`, `fundamentally` | cut, or state the fact |
| em dashes | two asides inside sentences | split into sentences |
| long sentences | two run-ons, worst over 40 words | one idea per sentence |

### Install and use

The installer detects Claude Code, Codex, Gemini CLI, Cursor, Windsurf, and Copilot. It installs the PATH commands and the matching writing skill. See [INSTALL.md](INSTALL.md) for options and manual setup.

```bash
curl -fsSL https://raw.githubusercontent.com/MichelKazi/slopbliterator/main/install.sh | sh
slop-lint < draft.txt
slop-lint pr.md notes.md
git diff origin/main...HEAD | slop-substance --body pr.txt --markdown
slop-lint --add banned "at the end of the day"
```

Target fewer than 1.5 violations per 100 words. Baseline AI writing scores about 4.4.

### How it works

Slopbliterator has two checks.

- **Form**: `slop-lint` checks sentence length, punctuation, voice, weak verbs, and banned terms. Fix each form flag.

- **Substance**: `slop-substance` detects PR text that repeats the diff. It reports a signal. You decide whether the text adds useful context.

The packaged word list stays read-only. `--add` stores personal terms in the user configuration directory.

### Make it yours

The base rules use a neutral voice. Add a `persona.md` file to restore a specific voice without weakening the rules.

Copy a file from `personas/` or write your own. No persona means neutral STE.

Use `--add` to store your own banned terms and replacements. Edit `SKILL.md` to change the writing rules.

### Enforce it

`hooks/precommit-slop-check.sh` checks a commit message before it lands. The hook is optional and advisory. See `hooks/README.md`.

### Limits and credit

The linter fixes the form of slop. It cannot make a hollow paragraph true. Do not use it for text that needs a distinct voice.

The STE approach and original linter come from [woosal1337's "the cure for AI slop"](https://github.com/woosal1337/blog/tree/main/videos/ep01-the-cure-for-ai-slop). Slopbliterator adds substance checks, an editable word list, and personas. MIT licensed.
