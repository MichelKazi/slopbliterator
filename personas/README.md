# Personas (optional voice layer)

Slopbliterator's base is voice-neutral on purpose. STE gives you clean, unambiguous FORM. It does not give you a personality, and by default it takes yours away.

A persona layers a voice back ON TOP of the STE floor. The floor still holds: short sentences, no slop, no em dashes, active voice, the substance test. The persona shapes stance and tone above that line.

## How to activate one

Copy the persona you want to the skill root as `persona.md`:

```
cp personas/tired-engineer.md persona.md
```

If `persona.md` exists at the skill root, the skill layers it on top of STE for outward text. If it does not exist, you get pure neutral STE. That is the whole mechanism: presence of the file.

To turn it off, delete `persona.md`. To switch, copy a different one over it.

## Write your own

A persona is a short markdown file, 3 to 6 bullets, describing stance and tone only. It must not fight the STE floor (do not ask for long sentences, em dashes, or marketing words). Good persona rules govern:

- What to lead with (the failure, the decision, the headline).
- What to cut (praise, hedging, restatement).
- How much warmth or bluntness.
- Whether to take positions or stay neutral.

Keep it to voice. The linters still enforce form; the substance test still enforces usefulness. The persona is the last layer, not a replacement for either.

## Included examples

Two ship with the skill. They are opt-in, and they double as templates for writing your own: copy one, edit the bullets, save it as `persona.md`.

- `tired-engineer.md` — blunt, time-respecting, leads with what failed. Take positions.
- `plain-neutral.md` — the default when no persona is set, written out so you can see the baseline.
