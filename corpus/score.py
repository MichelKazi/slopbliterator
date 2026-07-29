#!/usr/bin/env python3
"""Score labeled prose cases against both linters."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SETS = (("known-slop.jsonl", True), ("known-clean.jsonl", False))


def load_cases():
    """Load labeled cases from both corpus files."""
    cases = []
    for filename, expected in SETS:
        with (Path(__file__).parent / filename).open() as source:
            for line_number, line in enumerate(source, 1):
                if line.strip():
                    case = json.loads(line)
                    case["expected"] = expected
                    case["source"] = f"{filename}:{line_number}"
                    cases.append(case)
    return cases


def load_form_linter(config_home):
    """Load the form linter without user word-list overrides."""
    os.environ["XDG_CONFIG_HOME"] = str(config_home)
    spec = importlib.util.spec_from_file_location("ste_lint", ROOT / "ste-lint.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def form_result(module, case):
    """Return whether one form detector fired for a case."""
    result = module.lint(case["text"])
    detector = case["detector"]
    if detector == "em_dash(slop-marker)":
        return result[detector] > 0
    if detector == "marketing_triad(advisory)":
        return result.get("advisories", {}).get(detector, 0) > 0
    return result.get("violations", {}).get(detector, 0) > 0


def substance_result(case, directory):
    """Run the substance CLI and parse its stable detector labels."""
    body = directory / "body.txt"
    diff = directory / "diff.txt"
    body.write_text(case["text"])
    diff.write_text(case.get("diff", ""))
    output = subprocess.run(
        [sys.executable, str(ROOT / "substance-lint.py"), "--body", str(body), "--diff", str(diff), "--markdown"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    detector = case["detector"]
    checks = {
        "diff_narration": "[POSSIBLE NARRATION" in output,
        "result_restatement": "[COLLAPSE]" in output,
        "missing_substance": "weak/absent:" in output,
        "overexplanation": "over-explanation phrases: none" not in output,
        "unbackticked_symbol": "unbackticked code symbols: none" not in output,
    }
    return checks[detector]


def score(cases):
    """Return confusion counts and failing case IDs per detector."""
    results = {}
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        form = load_form_linter(directory / "config")
        for case in cases:
            actual = form_result(form, case) if case["linter"] == "ste" else substance_result(case, directory)
            key = f'{case["linter"]}:{case["detector"]}'
            row = results.setdefault(key, {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "false_positives": [], "false_negatives": []})
            if case["expected"] and actual:
                row["tp"] += 1
            elif case["expected"]:
                row["fn"] += 1
                row["false_negatives"].append(case["id"])
            elif actual:
                row["fp"] += 1
                row["false_positives"].append(case["id"])
            else:
                row["tn"] += 1
    for row in results.values():
        predicted = row["tp"] + row["fp"]
        positive = row["tp"] + row["fn"]
        row["precision"] = round(row["tp"] / predicted, 4) if predicted else None
        row["recall"] = round(row["tp"] / positive, 4) if positive else None
    return results


def print_report(results, baseline=None):
    """Print per-detector metrics and optional deltas."""
    print("detector                                      precision  recall   TP FP FN TN   delta(P/R)")
    for detector, row in sorted(results.items()):
        precision = "n/a" if row["precision"] is None else f'{row["precision"]:.2f}'
        recall = "n/a" if row["recall"] is None else f'{row["recall"]:.2f}'
        delta = ""
        if baseline and detector in baseline:
            old = baseline[detector]
            pd = None if row["precision"] is None or old["precision"] is None else row["precision"] - old["precision"]
            rd = None if row["recall"] is None or old["recall"] is None else row["recall"] - old["recall"]
            delta = f'{"n/a" if pd is None else f"{pd:+.2f}"}/{"n/a" if rd is None else f"{rd:+.2f}"}'
        print(f'{detector:45} {precision:>9} {recall:>7}   {row["tp"]:2d} {row["fp"]:2d} {row["fn"]:2d} {row["tn"]:2d}   {delta}')
        if row["false_positives"]:
            print(f'  false positives: {", ".join(row["false_positives"])}')
        if row["false_negatives"]:
            print(f'  false negatives: {", ".join(row["false_negatives"])}')


def main():
    """Score the corpus and print text or JSON output."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, help="JSON result from an earlier run")
    parser.add_argument("--json", action="store_true", help="print machine-readable results")
    args = parser.parse_args()
    results = score(load_cases())
    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        baseline = json.loads(args.baseline.read_text()) if args.baseline else None
        print_report(results, baseline)


if __name__ == "__main__":
    main()
