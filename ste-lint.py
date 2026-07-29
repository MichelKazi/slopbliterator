import re, sys, json, glob, os, tempfile

MARKETING = ["seamless","seamlessly","robust","powerful","cutting-edge","effortless","effortlessly",
    "world-class","next-generation","revolutionary","blazing","lightning-fast","elegant","delightful",
    "turnkey","best-in-class","state-of-the-art","game-changing","first-class","battle-tested",
    "enterprise-grade","supercharge","unlock","unleash","empower","empowers"]
BANNED = ["begin","begins","commence","commences","initiate","initiates","originate",
    "utilize","utilizes","utilizing","leverage","leverages","leveraging","facilitate","facilitates",
    "ensure","ensures","ensuring","prior to","subsequent to","obtain","obtains","acquire","acquires",
    "demonstrate","demonstrates","additionally","furthermore","moreover","comprehensive","comprehensively",
    "utilization","aforementioned","henceforth","therein","whilst","amongst","numerous","myriad","plethora",
    "in order to","a variety of","in the event that","due to the fact that","it is important to note",
    "smoking gun","load-bearing","load bearing","this means","as a result","going forward","testament to","delve"]
PHRASAL = ["spin up","spin down","reach out","dive into","dives into","diving into","kick off","kicks off",
    "roll out","rolls out","tear down","ramp up","circle back","drill down","spun up","reaching out"]
MODAL_HEDGE = ["it is important to note","it should be noted","it is worth noting","please note that",
    "as mentioned","as noted above"]
BE = r"(?:am|is|are|was|were|be|been|being)"
PP_IRREG = r"(?:done|made|sent|read|built|kept|held|set|put|run|written|shown|given|taken|found|got|gotten|seen|known|thrown|drawn)"

# Default banword file: {"banned": {phrase: [alts]}, "marketing": {...}, "phrasal": {...}}.
# User entries override its alternatives without changing the packaged file.
_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banned-words.json")
_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
_USER_DATA = os.path.join(_CONFIG_HOME, "slopbliterator", "banned-words.json")
ALTS = {}  # phrase -> [alternatives]
for _source in (_DATA, _USER_DATA):
    try:
        with open(_source) as _fh:
            _d = json.load(_fh)
        for _cat, _target in (("banned", BANNED), ("marketing", MARKETING), ("phrasal", PHRASAL)):
            for _ph, _alts in _d.get(_cat, {}).items():
                if _ph not in _target:
                    _target.append(_ph)
                ALTS[_ph] = _alts
    except (OSError, ValueError):
        pass  # fail open: hardcoded lists still work if either file is missing/broken


def suggest(phrase):
    alts = ALTS.get(phrase)
    if alts:
        return f"{phrase} -> {', or '.join(alts)}"
    if alts == []:
        return f"{phrase} -> (no drop-in; rephrase)"
    return phrase  # not in the data file, hardcoded-only

def strip_code(t):
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"`[^`]*`", " ", t)
    return t

def sentences(text):
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if not s: continue
        s = re.sub(r"^\s*#{1,6}\s*", "", s)
        s = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", s)
        if not s: continue
        parts = re.split(r"(?<=[.!?:])\s+(?=[A-Z0-9\"'\-])", s)
        for p in parts:
            p = p.strip()
            if p: out.append(p)
    return out

def wc(s):
    return len([w for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-/]*", s)])

def count_ci(text, phrases):
    n = 0; hits = []
    low = text.lower()
    for ph in phrases:
        for m in re.finditer(r"(?<![a-z])" + re.escape(ph) + r"(?![a-z])", low):
            n += 1; hits.append(ph)
    return n, hits

def lint(text):
    raw = text
    text = strip_code(text)
    sents = sentences(text)
    words = sum(wc(s) for s in sents) or 1
    v = {}
    longs = [(wc(s), s) for s in sents if wc(s) > 20]
    v["long_sentence(>20w)"] = len(longs)
    v["semicolon"] = text.count(";")
    v["contraction"] = len(re.findall(r"\b\w+['’](?:t|re|ve|ll|d|s|m)\b", text))
    v["passive_voice"] = len(re.findall(rf"\b{BE}\s+(?:\w+ed|{PP_IRREG})\b", text, re.I))
    v["ing_main_verb"] = len(re.findall(rf"\b{BE}\s+\w+ing\b", text, re.I))
    v["nominalization"] = len(re.findall(r"\b(?:perform(?:s|ed)?|conduct(?:s|ed)?|provide(?:s|d)?|carry out|carries out|make use of|makes use of)\b", text, re.I)) + len(re.findall(r"\b\w{4,}(?:tion|ment|ance|ence)\s+of\b", text, re.I))
    v["phrasal_verb"], _ = count_ci(text, PHRASAL)
    v["banned_word"], bh = count_ci(text, BANNED)
    v["marketing_adjective"], mh = count_ci(text, MARKETING)
    v["modal_hedge"], _ = count_ci(text, MODAL_HEDGE)
    paras = [p for p in re.split(r"\n\s*\n", raw) if p.strip()]
    v["long_paragraph(>6s)"] = sum(1 for p in paras if len(sentences(strip_code(p))) > 6)
    em = raw.count("—") + raw.count("–")
    total = sum(v.values())
    per100 = {k: round(x*100.0/words, 2) for k, x in v.items()}
    return {
        "words": words, "sentences": len(sents),
        "violations": v, "total": total,
        "total_per100w": round(total*100.0/words, 2),
        "em_dash(slop-marker)": em,
        "longest_sentence_words": (max(longs)[0] if longs else max((wc(s) for s in sents), default=0)),
        "sample_marketing": list(dict.fromkeys(mh))[:6],
        "sample_banned": list(dict.fromkeys(bh))[:6],
        "suggestions": [suggest(p) for p in dict.fromkeys(bh + mh)],
    }

def add_entry(category, phrase, alts):
    """Add a banned phrase and its alternatives to the user word list."""
    if category not in ("banned", "marketing", "phrasal"):
        print(f"category must be banned|marketing|phrasal, got {category!r}"); sys.exit(2)
    try:
        with open(_USER_DATA) as fh: d = json.load(fh)
    except (OSError, ValueError):
        d = {"banned": {}, "marketing": {}, "phrasal": {}}
    d.setdefault(category, {})[phrase.lower()] = [a.lower() for a in alts]
    os.makedirs(os.path.dirname(_USER_DATA), exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=os.path.dirname(_USER_DATA), delete=False) as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False); fh.write("\n")
        pending = fh.name
    os.replace(pending, _USER_DATA)
    print(f"added [{category}] {phrase!r} -> {alts or '(rephrase)'}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--add":
        # ste-lint.py --add <category> "<phrase>" ["alt1" "alt2" ...]
        if len(sys.argv) < 4:
            print('usage: ste-lint.py --add <banned|marketing|phrasal> "<phrase>" ["alt" ...]'); sys.exit(2)
        add_entry(sys.argv[2], sys.argv[3], sys.argv[4:]); sys.exit(0)
    files = sys.argv[1:] or []
    if not files:
        print(json.dumps(lint(sys.stdin.read()), indent=2)); sys.exit(0)
    exp = []
    for f in files: exp += sorted(glob.glob(f)) if any(c in f for c in "*?[") else [f]
    for f in exp:
        with open(f) as fh: r = lint(fh.read())
        print(f"{os.path.basename(f):32} words={r['words']:4d} total={r['total']:3d} per100w={r['total_per100w']:6.2f} em_dash={r['em_dash(slop-marker)']:2d}")
