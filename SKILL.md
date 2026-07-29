---
name: slopbliterator
description: Rewrite prose (docs, READMEs, PR descriptions, commit bodies, error messages, release notes, comments, never code) into ASD-STE100 Simplified Technical English to remove AI slop. Use when writing or polishing outward text, when asked to make writing not sound like AI, make docs plain, or enforce a clear writing style. Ships a deterministic linter (ste-lint.py) to score the result. Two modes: strict (procedures/errors) and STE-flavored (general prose).
---

# Slopbliterator (STE writing)

Slop is not a vocabulary problem you fix by banning one word at a time. It is a FORM problem: ambiguity with good posture. The fix is a writing system the model can check itself against, not a blacklist. This skill uses ASD-STE100 Simplified Technical English, a controlled-language standard built in 1986 so aircraft mechanics never misread a manual. Tested across models it cuts slop about 74 percent, versus about 3 percent for a banned-word list.

Applies to prose: docs, READMEs, PR and commit bodies, error messages, release notes, comments, agent output. NOT code, identifiers, or command syntax. NOT marketing copy or anything that needs a voice. STE strips voice on purpose.

## The six habits of slop (name it, then kill it)

1. Synonym rotation: same thing called three names (user / customer / client). Pick one name, use it every time.
2. Hedging stacks: helper verbs pile up and nothing happens. "It is important to note that this may potentially help to improve." Cut to "this improves X."
3. Frozen verbs (nominalization): "perform an analysis of" for "analyze", "provides assistance" for "helps". Use the verb.
4. Marketing adjectives: seamless, robust, powerful, cutting-edge, effortless. They claim quality instead of showing it. Delete, or state the fact.
5. Run-on sentences: four ideas stitched with em dashes and semicolons. Make four sentences.
6. Chatty phrasal verbs: spin up, reach out, dive into, kick off. Use a plain verb (start, contact, read, begin).

## Rules

WORDS
- One name for one thing. One meaning per word ("fall" means move down, never "decrease").
- Short common word: start (not begin/commence/initiate), use (not utilize/leverage), help (not facilitate), make sure (not ensure), before (not prior to), after (not subsequent to), about (not regarding), get (not obtain), show (not demonstrate), also (not additionally/furthermore/moreover).
- No marketing adjectives. American spelling.

VERBS
- Active voice. "the parser reads the file", not "the file is read by the parser".
- A verb for an action. "analyze the log", not "perform an analysis of the log".
- No stacked auxiliaries. No "-ing" main verb where a simple tense works.

SENTENCES
- One idea per sentence. Max 20 words (instruction), max 25 (descriptive).
- No contractions. Use articles (a, an, the, this).

PUNCTUATION
- No semicolons. Write two sentences.
- No em dashes (— or –). Use a comma, or split the sentence. (STE bans only the semicolon. The em-dash ban is the house rule from CLAUDE.md.)

BANNED TELLS (house additions)
- Never: "smoking gun", "load-bearing", "ensures that", "this means", "in order to", "as a result", "going forward", "it's important to note", "delve", "tapestry", "testament to".
- No sycophantic openers ("Great question", "Absolutely", "Certainly"). No performative helpfulness ("I'd be happy to", "hope this helps"). No conclusion filler ("In conclusion", "To summarize", "The key takeaway").

CODE SYMBOLS
- Wrap every code symbol in single backticks, in all outward text INCLUDING commit messages: variable, method, class, field, flag, file path, constant, RPC name. `user.active?`, `set_visibility`, `feature-flag-name`, `app/models/user.rb`.
- Commit messages ban code FENCES (```) and other markdown (bullets, headers, bold), but single backticks around a symbol are fine and expected.

STRUCTURE
- One topic per paragraph, max six sentences. For steps: numbered vertical list, one action per item, imperative form. Condition before command.
- Break the rule of three. Do not default to three bullets or three adjectives. Use two, or four, or one.
- No "not just X, but also Y." No bold-keyword-colon pattern in lists. Headers are tools, not decoration.
- Take positions. If one option is better, say so. Do not hedge everything equally.
- Write only the requested text. No preamble, no restating the question, no closing summary.

## Modes

- strict: procedures, runbooks, safety text, error messages. Apply every rule and both length caps.
- STE-flavored: general prose (READMEs, PR and commit bodies, docs). Keep the sentence, paragraph, active-voice, and no-phrasal-verb discipline. Relax the dictionary lockdown so the text keeps enough range to read naturally. Default to this for most work.

Note: STE is for technical and outward text. Casual conversation can relax the no-contraction and length caps. The six habits, marketing adjectives, banned tells, and em-dash ban still apply everywhere.

Order of operations: draft in STE-flavored, run the substance test below, then run the linter and fix what it flags. The linter guards form. The substance test guards whether the text is worth reading. Both, every time, for outward text.

## Persona layer (optional voice, off by default)

The base skill is voice-neutral on purpose. If a file named `persona.md` exists at the skill root, layer it on top of the STE floor for outward text: apply its stance and tone AFTER form and substance are satisfied. The persona never relaxes the floor. It cannot ask for long sentences, em dashes, marketing words, or slop. It shapes only what to lead with, what to cut, and how much warmth or bluntness.

If there is no `persona.md`, write plain neutral STE. That is the correct default for error messages, API docs, and anything where clarity is the whole job.

Ready-made personas and instructions to write your own are in `personas/`. Activate one by copying it to the skill root as `persona.md`.

## Substance test (PR/commit descriptions, issues, review comments)

Respect the reader's time. A reviewer stops reading a description the moment it becomes a tour of the diff, because it will not teach them anything the diff will not. The reader's test: does this sentence tell me something reading the code would not? If no, cut it. Lead with what failed, what is unimplemented, or a decision you made without asking. Never a rosy summary that buries them.

Every sentence must earn its place as one of these four:
1. WHY: the problem, the incident, the reason this exists. Not what changed.
2. TRADE-OFF or DECISION: why this approach over the alternative, what you chose not to do, why.
3. NON-OBVIOUS CONSEQUENCE: a behavioral interaction, a scope boundary, a follow-up, a thing that looks like a bug but is not, a guarantee a reviewer must verify.
4. VERIFICATION: how you know it works, what you tested, what you could not.

Two failure modes, opposite directions. Narration says too little (restates the diff). Over-explanation says too much (pads with instructions, warnings, and obvious outcomes). Both read like AI. Cut both.

Cut on sight, narration (too little):
- Diff narration: "Adds a setX mutation taking a and b", "Plumbs updateX through the store and setX through the manager", "Exposes Y on the read model, regenerates the schema". The reviewer sees the layers by opening the diff. Say WHY it is split that way, or say nothing.
- Restating the title or the ticket.

Cut on sight, over-explanation (too much):
- Instructing the reviewer: "Verify in review that...", "Note that...", "Please check...", "Keep in mind...". State the fact as a plain declarative and trust the reviewer to review. "X is admin-only" not "Verify in review that X is admin-only."
- Manufactured warnings: a "WATCH OUT" or "this could be a bug" for behavior that is almost certainly intended. Only flag a risk you actually believe is a risk. A default value or a documented behavior is not a warning.
- A Result section that restates the Modification, or states the obvious ("no client-facing change, live on merge", "the tests pass"). Most PRs do not need a Result section. Write one only when the observable outcome is not obvious from the change. When in doubt, delete it.
- Hedged over-qualification: "this should", "in most cases", "generally" stacked onto a fact you are sure of.

Litmus for a Modification/Solution section: if you deleted it and made the reviewer read the diff, what would they NOT know? Write exactly that, as plain declaratives. If the answer is "nothing", the section is one line or gone. Do not pad it back up with reviewer instructions or warnings to hit a length.

Deterministic check for diff-narration (the mechanizable part of this test):

```
git diff origin/main...HEAD | python3 substance-lint.py --body pr.txt
```

It flags: (1) diff-symbol overlap: what fraction of the symbols your Modification names also appear in the diff, over 60% is possible narration; (2) Result-restates-Modification word overlap; (3) which of why/trade-off/consequence signals are present.

This lint is a SIGNAL, not a verdict. False positives are expected. Two common ones: a PR whose whole point is a new public API (naming the new symbols IS the useful information for a consumer), and a tiny diff where restating it costs the reader nothing. When it flags, do not act on the number. Judge it against the real change, then act by confidence:

- If you are confident the flag is right (the section really is a diff tour, and a reviewer would learn nothing from it): rewrite it by the four-category rule and say you did, one line, with what you changed.
- If it is borderline, or you think it is a false positive: do not rewrite silently. Show the reader the flag, name why you think it is or is not real, and offer a proposed rewrite for them to accept or reject.
- If you judge it a clear false positive (the symbols ARE the point, or the diff is trivial): say so in one line and leave the text. Do not rewrite to satisfy the linter.

The linter proves a description CAN be diff narration. Only you can judge whether it is, given what the change actually is.

Worked example of the failure: "Plumbs a partial-column `updateVisibility` through the store and a `setVisibility` through the manager" is diff narration. The reviewer sees the store and manager layers in the diff. The useful version answers the code-invisible questions: why partial-column (a `None` argument must not overwrite the other flag), and how the two fields are kept off the client schema (the one thing the reviewer must verify and cannot see at a glance).

## Self-lint (deterministic, run before returning text)

The linter scores violations per 100 words. Lower is cleaner. STE target is about 1.1. Baseline AI writing is about 4.4.

```
python3 ste-lint.py < draft.txt        # stdin, JSON out
python3 ste-lint.py file1.md file2.md  # table over files
```

Then fix by hand what it flags:
1. Any sentence over 20 words? Split it.
2. Any semicolon or em dash? Replace with a period or comma.
3. Any contraction? Expand it.
4. Any passive voice with a known actor? Make it active.
5. Any "-ing" main verb, nominalization, or phrasal verb? Plain verb.
6. Same thing named two ways? Pick one name.

On a banned-word or marketing-word hit, the linter prints suggested alternatives (from `banned-words.json`). Do NOT stop and ask which to use. A one-word swap in a draft is maximally reversible. Take the obvious curated alternative, or a plain synonym if none fit, or rephrase the sentence. Just make the swap and move on. If the choice is genuinely load-bearing (rare for a single word), flag it inline in one line ("used `use` for `leverage`") so the reader can override. Reserve blocking questions for real forks, not word choice.

Grow the list as you go: when the reader rejects a word or you spot a new slop tell, `python3 ste-lint.py --add <banned|marketing|phrasal> "<phrase>" ["alt" ...]`. Next draft is scored against it with the alternative pre-chosen.

The linter catches the mechanical form of slop. That is where the quality loss lives and it is fully checkable. It cannot judge whether the content is true or worth saying. STE fixes bad writing, not "nothing to say." Keep it away from anything that needs a voice.

Standard (free, copyrighted, do not paste in full): https://asd-ste100.org
