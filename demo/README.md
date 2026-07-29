# Demo

Reproduce the numbers in the top-level README:

```
python3 ../ste-lint.py before.md after.md
```

`before.md` takes real technical facts (an H.264 / VideoToolbox encoder quirk) and writes them the way an LLM would: em dashes, "load-bearing", "it's important to note", marketing words. Every claim is true. It scores 18.39 violations per 100 words. `after.md` is the same facts in STE, at 0.00.

The point: you do not need a badly-researched paragraph to make slop. Correct content, written loose, is still slop. This fixes the form.
