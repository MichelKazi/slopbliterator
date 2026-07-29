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
CONTRACTION = re.compile(
    r"\b(?:\w+['’](?:t|re|ve|ll|d|m)|(?:it|that|what|there|here|who|he|she|let)['’]s)\b",
    re.I,
)
PASSIVE = re.compile(rf"\b{BE}\s+(?P<participle>\w+ed|{PP_IRREG})\b", re.I)
ADJECTIVAL_PARTICIPLES = {"based", "closed", "excited", "interested", "used"}
ING_ADJECTIVES = {"interesting", "missing", "promising"}
NOT_JUST = re.compile(
    r"\b(?:(?<!did )(?<!does )(?<!do )not\s+(?:just|only|merely|simply)\b[^.!?\n]{1,120}?\bbut(?:\s+also)?\b"
    r"|it(?:['’]s| is)\s+not\s+about\b[^.!?\n]{1,120}?,\s*it(?:['’]s| is)\s+about\b"
    r"|isn['’]t\s+just\b[^.!?\n]{1,120}?,\s*it(?:['’]s| is)\b)",
    re.I,
)
TRIAD = re.compile(
    r"\b(?P<a>[A-Za-z][A-Za-z-]*(?:\s+[A-Za-z][A-Za-z-]*){0,3}),\s*"
    r"(?P<b>[A-Za-z][A-Za-z-]*(?:\s+[A-Za-z][A-Za-z-]*){0,3}),\s*"
    r"and\s+(?P<c>[A-Za-z][A-Za-z-]*(?:\s+[A-Za-z][A-Za-z-]*){0,3})\b",
    re.I,
)
COMPLEX_VERB = re.compile(
    rf"\b(?:has|have|had)\s+(?:been\s+)?(?:\w+ed|{PP_IRREG})\b|\b(?:will|shall)\s+be\s+\w+ing\b",
    re.I,
)
NUMBERED_STEP = re.compile(r"^\s*\d+[.)]\s+(?P<step>\S.*)$", re.M)
NON_IMPERATIVE_STEP = re.compile(r"^(?:you\s+(?:can|must|should|will)|(?:a|an|the|this|these|it|we)\b)", re.I)
NOTE_INSTRUCTION = re.compile(
    r"^\s*NOTE:\s*(?:check|close|connect|disconnect|do|install|make|open|pull|push|put|read|remove|run|select|set|start|stop|turn|use|write)\b",
    re.I | re.M,
)
BRITISH_SPELLINGS = {
    "analyse": "analyze", "analysed": "analyzed", "analysing": "analyzing",
    "behaviour": "behavior", "centre": "center", "centred": "centered",
    "colour": "color", "coloured": "colored", "fibre": "fiber",
    "licence": "license", "modelling": "modeling", "organise": "organize",
    "organised": "organized", "organising": "organizing", "programme": "program",
}
VALID_MODES = ("flavored", "procedure", "descriptive")

# Default banword file: {"banned": {phrase: [alts]}, "marketing": {...}, "phrasal": {...}}.
# User entries override its alternatives without changing the packaged file.
_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banned-words.json")
_RULES_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ste-rules.json")
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
    t = re.sub(r"\A---\s*\n(?=[A-Za-z_][\w-]*:\s).*?\n---\s*(?:\n|$)", " ", t, flags=re.S)
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"`[^`]*`", " ", t)
    return t

def strip_quoted_text(t):
    """Remove text that can preserve an official or user-interface spelling."""
    t = re.sub(r'"[^"\n]*"|“[^”\n]*”', " ", t)
    return re.sub(r"^\s*>.*$", " ", t, flags=re.M)

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

def ste_wc(s):
    """Count clear Issue 9 special elements as one word."""
    s = re.sub(r"\([^()\n]*\)", " STEWORD ", s)
    s = re.sub(r'"[^"\n]*"|“[^”\n]*”', " STEWORD ", s)
    s = re.sub(r"\b\d+(?:[.,]\d+)?\s*(?:°?[A-Za-z%]+(?:/[A-Za-z]+)?)\b", " STEWORD ", s)
    return wc(s)

def count_ci(text, phrases):
    n = 0; hits = []
    low = text.lower()
    for ph in phrases:
        for m in re.finditer(r"(?<![a-z])" + re.escape(ph) + r"(?![a-z])", low):
            n += 1; hits.append(ph)
    return n, hits

def count_passives(text):
    """Count likely passive constructions, excluding common predicate adjectives."""
    count = 0
    for match in PASSIVE.finditer(text):
        participle = match.group("participle").lower()
        if participle not in ADJECTIVAL_PARTICIPLES or (participle == "used" and re.match(r"\s+by\b", text[match.end():], re.I)):
            count += 1
    return count

def count_ing_main_verbs(text):
    """Count BE plus gerund forms, excluding common predicate adjectives."""
    matches = re.finditer(rf"\b{BE}\s+(?P<gerund>\w+ing)\b", text, re.I)
    return sum(1 for match in matches if match.group("gerund").lower() not in ING_ADJECTIVES)

def count_marketing_triads(text):
    """Count short triads where at least two items contain marketing terms."""
    count = 0
    for match in TRIAD.finditer(text):
        items = (match.group("a"), match.group("b"), match.group("c"))
        if sum(count_ci(item, MARKETING)[0] > 0 for item in items) >= 2:
            count += 1
    return count

def count_non_imperative_steps(text):
    """Count numbered procedure steps that clearly start as statements."""
    return sum(1 for match in NUMBERED_STEP.finditer(text) if NON_IMPERATIVE_STEP.match(match.group("step")))

def is_vertical_list(text):
    """Return true when a block is a list, with an optional introductory line."""
    lines = [line for line in text.splitlines() if line.strip()]
    list_lines = sum(bool(re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", line)) for line in lines)
    return list_lines >= 2 and list_lines >= len(lines) - 1

def load_rule_manifest():
    """Load and validate the Issue 9 rule coverage manifest."""
    with open(_RULES_DATA) as source:
        manifest = json.load(source)
    rules = manifest.get("rules", [])
    expected = manifest.get("standard", {}).get("rule_count")
    ids = [rule.get("id") for rule in rules]
    if expected != 53 or len(rules) != expected or len(set(ids)) != expected:
        raise ValueError("ste-rules.json must contain 53 unique Issue 9 rules")
    return manifest

def lint(text, mode="flavored"):
    """Return scored violations and unscored advisories for one text."""
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of: {', '.join(VALID_MODES)}")
    raw = text
    text = strip_code(text)
    sents = sentences(text)
    word_count = wc if mode == "flavored" else ste_wc
    words = sum(word_count(s) for s in sents) or 1
    v = {}
    sentence_limit = 25 if mode == "descriptive" else 20
    long_label = f"long_sentence(>{sentence_limit}w)"
    longs = [(word_count(s), s) for s in sents if word_count(s) > sentence_limit]
    v[long_label] = len(longs)
    v["semicolon"] = text.count(";")
    v["contraction"] = len(CONTRACTION.findall(text))
    v["passive_voice"] = count_passives(text)
    v["ing_main_verb"] = count_ing_main_verbs(text)
    v["nominalization"] = len(re.findall(r"\b(?:perform(?:s|ed)?|conduct(?:s|ed)?|provide(?:s|d)?|carry out|carries out|make use of|makes use of)\b", text, re.I))
    v["phrasal_verb"], _ = count_ci(text, PHRASAL)
    v["banned_word"], bh = count_ci(text, BANNED)
    v["marketing_adjective"], mh = count_ci(text, MARKETING)
    v["modal_hedge"], _ = count_ci(text, MODAL_HEDGE)
    v["not_just_but"] = len(NOT_JUST.findall(text))
    paras = [p for p in re.split(r"\n\s*\n", raw) if p.strip()]
    v["long_paragraph(>6s)"] = sum(
        1 for p in paras if not is_vertical_list(p) and len(sentences(strip_code(p))) > 6
    )
    em = raw.count("—")
    triads = count_marketing_triads(text)
    spelling_text = strip_quoted_text(text)
    spelling_count, spelling_hits = count_ci(spelling_text, BRITISH_SPELLINGS)
    complex_verbs = len(COMPLEX_VERB.findall(text))
    non_imperative_steps = count_non_imperative_steps(text) if mode == "procedure" else 0
    note_instructions = len(NOTE_INSTRUCTION.findall(text)) if mode == "procedure" else 0
    messages = []
    if triads:
        messages.append("possible marketing triad, judge it")
    if spelling_count:
        messages.append("possible non-American spelling, check applicable directives")
    if complex_verbs:
        messages.append("possible complex verb, judge its tense and meaning")
    if non_imperative_steps:
        messages.append("possible non-imperative procedure step, judge it")
    if note_instructions:
        messages.append("possible instruction in a note, move the action to a step")
    advisories = {
        "marketing_triad(advisory)": triads,
        "american_spelling(advisory)": spelling_count,
        "complex_verb(advisory)": complex_verbs,
        "non_imperative_step(advisory)": non_imperative_steps,
        "instruction_in_note(advisory)": note_instructions,
        "messages": messages,
        "sample_non_american_spelling": list(dict.fromkeys(spelling_hits))[:6],
        "spelling_suggestions": [
            f"{spelling} -> {BRITISH_SPELLINGS[spelling]}"
            for spelling in list(dict.fromkeys(spelling_hits))[:6]
        ],
    }
    total = sum(v.values())
    per100 = {k: round(x*100.0/words, 2) for k, x in v.items()}
    return {
        "words": words, "sentences": len(sents), "mode": mode, "sentence_limit": sentence_limit,
        "violations": v, "total": total,
        "total_per100w": round(total*100.0/words, 2),
        "em_dash(slop-marker)": em,
        "advisories": advisories,
        "longest_sentence_words": (max(longs)[0] if longs else max((word_count(s) for s in sents), default=0)),
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
    if len(sys.argv) > 1 and sys.argv[1] == "--coverage":
        try:
            print(json.dumps(load_rule_manifest(), indent=2)); sys.exit(0)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"cannot load STE coverage: {error}", file=sys.stderr); sys.exit(2)
    mode = "flavored"
    files = []
    args = sys.argv[1:]
    index = 0
    while index < len(args):
        if args[index] == "--mode":
            if index + 1 >= len(args):
                print("--mode requires flavored|procedure|descriptive", file=sys.stderr); sys.exit(2)
            mode = args[index + 1]
            index += 2
        else:
            files.append(args[index])
            index += 1
    if mode not in VALID_MODES:
        print(f"mode must be one of: {', '.join(VALID_MODES)}", file=sys.stderr); sys.exit(2)
    if not files:
        print(json.dumps(lint(sys.stdin.read(), mode), indent=2)); sys.exit(0)
    exp = []
    for f in files: exp += sorted(glob.glob(f)) if any(c in f for c in "*?[") else [f]
    for f in exp:
        with open(f) as fh: r = lint(fh.read(), mode)
        print(f"{os.path.basename(f):32} words={r['words']:4d} total={r['total']:3d} per100w={r['total_per100w']:6.2f} em_dash={r['em_dash(slop-marker)']:2d}")
