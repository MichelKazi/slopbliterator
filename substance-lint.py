#!/usr/bin/env python3
"""
substance-lint: a deterministic proxy for the reader's test — "does this PR
description say anything the diff does not?"

It cannot judge truth or insight. It flags the mechanical failure mode: a
Modification/Solution section that is just the diff's own identifiers rearranged
into English (diff narration), plus two cheaper checks.

Usage:
  substance-lint.py --body pr.txt --diff <(git diff origin/main...HEAD)
  git diff origin/main...HEAD | substance-lint.py --body pr.txt
Exit code 0 always; this is advisory. Read the flags, then use judgment.
"""
import re, sys, argparse

# camelCase, snake_case, dotted.paths, CONSTANTS, PascalCase — the tokens that
# identify code. Plain English words are excluded by requiring an internal
# capital, underscore, or dot (i.e. it looks like a symbol, not a word).
SYMBOL = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*(?:[A-Z_.][A-Za-z0-9_.]*)+\b")
ACRONYMS = {"GraphQL"}

# Over-explanation: instructing the reviewer, manufactured warnings, padding.
OVEREXPLAIN = [
    "verify in review", "please verify", "please check", "please note", "note that",
    "keep in mind", "be aware", "make sure to", "reviewer should", "you should verify",
    "watch out", "watch on deploy", "heads up", "worth noting", "it is worth",
    "for reference", "as a reminder", "just to be clear", "to be clear",
]
WHY      = re.compile(r"\b(because|so that|since|was never|stayed|used to|previously|incident|the problem|there was no|could not|would not|meant that)\b", re.I)
TRADEOFF = re.compile(r"\b(instead of|rather than|not a |not one |on purpose|chose|we could have|the alternative|to avoid|prevents|so a |so an )\b", re.I)
CONSEQ   = re.compile(r"\b(verify|tested|test that|flag|toggle|rollback|fall(?:s)? back|leak|guarantee|only|does not|blocked on|follow-?up|edge case|looks like)\b", re.I)


def section(body, name):
    # Grab text under a "Name:" header until the next header or end.
    m = re.search(rf"{name}[^\n:]*:\s*(.*?)(?=\n[A-Z][^\n:]*:|\Z)", body, re.S | re.I)
    return (m.group(1).strip() if m else "")


def symbols(text):
    return set(m.group(0) for m in SYMBOL.finditer(text))


def content_tokens(text):
    # lowercase alpha words >=4 chars, minus code fences/inline code
    text = re.sub(r"`[^`]*`", " ", text)
    return set(w for w in re.findall(r"[a-z]{4,}", text.lower()))


def unbackticked_symbols(text):
    # Symbols in prose NOT already inside backticks or a fenced block.
    # Blank out fenced blocks and inline code, then find bare symbols.
    masked = re.sub(r"```.*?```", " ", text, flags=re.S)
    masked = re.sub(r"`[^`]*`", " ", masked)
    # Drop markdown links and bare URLs (paths in URLs are not code refs).
    masked = re.sub(r"https?://\S+", " ", masked)
    found = [
        m.group(0) for m in SYMBOL.finditer(masked)
        if not ((m.group(0).isalpha() and m.group(0).isupper()) or m.group(0) in ACRONYMS)
    ]
    # Ignore sentence-start dotted things and version-y tokens are still symbols;
    # keep it simple, report uniques.
    return list(dict.fromkeys(found))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--diff", default=None, help="diff file; omit to read diff from stdin")
    ap.add_argument("--markdown", action="store_true",
                    help="check for unbackticked code symbols. Applies to all outward text including commit messages (symbols get backticks everywhere; only code fences are commit-banned).")
    a = ap.parse_args()

    body = open(a.body).read()
    if a.diff:
        diff = open(a.diff).read()
    else:
        diff = "" if sys.stdin.isatty() else sys.stdin.read()

    diff_syms = symbols(diff)
    mod = section(body, "Modification") or section(body, "Solution") or section(body, "What")
    result = section(body, "Result")

    print("== substance-lint (advisory heuristic) ==")

    # 1. Diff-narration: fraction of the Modification's SYMBOLS that also appear
    #    verbatim in the diff. High = the prose is naming code the reviewer sees.
    if mod and diff_syms:
        msyms = symbols(mod)
        if msyms:
            overlap = len(msyms & diff_syms) / len(msyms)
            verdict = "POSSIBLE NARRATION — judge it" if overlap >= 0.6 else "ok"
            print(f"1. diff-symbol overlap in Modification: {overlap:.0%} of its symbols are in the diff  [{verdict}]")
            if overlap >= 0.6:
                print("   -> Signal, not a verdict. High overlap OFTEN means diff narration, but not always:")
                print("      a PR whose point IS the new public API, or a tiny diff, can legitimately name")
                print("      its symbols. Judge against the actual change before acting (see skill protocol).")
    elif not diff_syms:
        print("1. diff-symbol overlap: SKIPPED (no diff provided — pipe `git diff` in)")

    # 2. Result restates Modification: content-word overlap.
    if mod and result:
        mt, rt = content_tokens(mod), content_tokens(result)
        if rt:
            ov = len(mt & rt) / len(rt)
            verdict = "COLLAPSE" if ov >= 0.5 else "ok"
            print(f"2. Result vs Modification word overlap: {ov:.0%}  [{verdict}]")
            if ov >= 0.5:
                print("   -> Result largely repeats Modification. State the observable outcome and")
                print("      the flag/rollback state, not a summary of the change.")

    # 3. Category signals present anywhere in the body (weak proxy for substance).
    hits = [n for n, rx in (("why", WHY), ("trade-off", TRADEOFF), ("consequence/verify", CONSEQ)) if rx.search(body)]
    missing = [n for n in ("why", "trade-off", "consequence/verify") if n not in hits]
    print(f"3. category signals present: {hits or 'NONE'}")
    if missing:
        print(f"   -> weak/absent: {missing}. A useful description usually carries why + a decision +")
        print("      a consequence or verification. Absence is a smell, not proof.")

    # 4. Over-explanation: reviewer instructions and manufactured warnings.
    low = body.lower()
    oe = [ph for ph in OVEREXPLAIN if ph in low]
    if oe:
        print(f"4. over-explanation phrases ({len(oe)}): {', '.join(oe)}")
        print("   -> State the fact as a plain declarative, do not instruct the reviewer or")
        print("      manufacture a warning. \"X is admin-only\", not \"Verify in review that X...\".")
    else:
        print("4. over-explanation phrases: none")

    # 5. Unbackticked code symbols (markdown-rendered text only).
    if a.markdown:
        bare = unbackticked_symbols(body)
        if bare:
            print(f"5. unbackticked code symbols ({len(bare)}): {', '.join(bare[:12])}{' ...' if len(bare) > 12 else ''}")
            print("   -> Wrap code symbols in backticks (all outward text, commits included).")
            print("      Judge ambiguous names against the code before changing prose.")
        else:
            print("4. unbackticked code symbols: none")

    print("\nThis is a proxy that flags POSSIBLE problems, not a verdict. False positives are")
    print("expected. If it flags, judge against the real change, then: rewrite only if you are")
    print("confident the flag is right; otherwise show the reader the flag and a proposed rewrite")
    print("and let them decide. Never silently rewrite on a borderline flag.")


if __name__ == "__main__":
    main()
