import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FORM_LINTER = ROOT / "ste-lint.py"
WORD_LIST = ROOT / "banned-words.json"
RULE_MANIFEST = ROOT / "ste-rules.json"
CORPUS_SCORER = ROOT / "corpus" / "score.py"
README = ROOT / "README.md"


def run_form_linter(script, *args, input_text=None, env=None):
    """Run one copy of the form linter and return its output."""
    return subprocess.run(
        [sys.executable, str(script), *args],
        input=input_text,
        text=True,
        capture_output=True,
        check=True,
        env=env,
    ).stdout


class FormLinterTests(unittest.TestCase):
    def test_issue_9_manifest_is_complete(self):
        """Keep every numbered Issue 9 rule in the coverage model."""
        manifest = json.loads(run_form_linter(FORM_LINTER, "--coverage"))
        expected = {
            *(f"1.{number}" for number in range(1, 15)),
            *(f"2.{number}" for number in range(1, 3)),
            *(f"3.{number}" for number in range(1, 8)),
            *(f"4.{number}" for number in range(1, 6)),
            *(f"5.{number}" for number in range(1, 6)),
            *(f"6.{number}" for number in range(1, 7)),
            *(f"7.{number}" for number in range(1, 4)),
            *(f"8.{number}" for number in range(1, 8)),
            *(f"9.{number}" for number in range(1, 5)),
        }

        self.assertEqual(manifest["standard"]["issue"], 9)
        self.assertEqual({rule["id"] for rule in manifest["rules"]}, expected)
        self.assertEqual(len(manifest["rules"]), 53)
        self.assertEqual(
            {rule["automation"] for rule in manifest["rules"]},
            {"enforced", "advisory", "manual"},
        )

    def test_demo_scores_match_baseline(self):
        """Keep the current form-linter scores stable."""
        before = json.loads(run_form_linter(FORM_LINTER, input_text=(ROOT / "demo/before.md").read_text()))
        after = json.loads(run_form_linter(FORM_LINTER, input_text=(ROOT / "demo/after.md").read_text()))

        self.assertEqual(before["total_per100w"], 19.54)
        self.assertEqual(after["total_per100w"], 0.0)

    def test_readme_scores_match_embedded_diff(self):
        """Keep the displayed README scores tied to its exact example."""
        readme = README.read_text()
        block = re.search(r"```diff\n(.*?)\n```", readme, re.S).group(1)
        before_text = " ".join(line[2:] for line in block.splitlines() if line.startswith("- "))
        after_text = " ".join(line[2:] for line in block.splitlines() if line.startswith("+ "))
        displayed = re.search(r"first version scores \*\*(\d+\.\d+)\*\*.*second scores \*\*(\d+\.\d+)\*\*", readme)

        before = json.loads(run_form_linter(FORM_LINTER, input_text=before_text))
        after = json.loads(run_form_linter(FORM_LINTER, input_text=after_text))

        self.assertEqual(float(displayed.group(1)), before["total_per100w"])
        self.assertEqual(float(displayed.group(2)), after["total_per100w"])

    def test_add_persists_across_simulated_reinstall(self):
        """Keep user entries after an installed payload is replaced."""
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            config_home = temp / "config"
            first_install = temp / "first"
            second_install = temp / "second"
            first_install.mkdir()
            second_install.mkdir()

            for install in (first_install, second_install):
                shutil.copy2(FORM_LINTER, install / FORM_LINTER.name)
                shutil.copy2(WORD_LIST, install / WORD_LIST.name)

            default_hash = hashlib.sha256(WORD_LIST.read_bytes()).hexdigest()
            env = os.environ.copy()
            env["XDG_CONFIG_HOME"] = str(config_home)

            run_form_linter(
                first_install / FORM_LINTER.name,
                "--add",
                "banned",
                "purple stapler",
                "plain words",
                env=env,
            )

            user_file = config_home / "slopbliterator" / "banned-words.json"
            user_data = json.loads(user_file.read_text())
            self.assertEqual(user_data["banned"]["purple stapler"], ["plain words"])
            self.assertEqual(hashlib.sha256(WORD_LIST.read_bytes()).hexdigest(), default_hash)
            self.assertEqual(
                hashlib.sha256((first_install / WORD_LIST.name).read_bytes()).hexdigest(),
                default_hash,
            )

            shutil.rmtree(first_install)
            result = json.loads(
                run_form_linter(
                    second_install / FORM_LINTER.name,
                    input_text="Purple stapler wastes time.",
                    env=env,
                )
            )

            self.assertEqual(result["violations"]["banned_word"], 1)
            self.assertIn("purple stapler -> plain words", result["suggestions"])
            self.assertEqual(
                hashlib.sha256((second_install / WORD_LIST.name).read_bytes()).hexdigest(),
                default_hash,
            )

    def test_user_alternative_overrides_packaged_default(self):
        """Prefer a user alternative for a packaged phrase."""
        with tempfile.TemporaryDirectory() as directory:
            env = os.environ.copy()
            env["XDG_CONFIG_HOME"] = directory

            run_form_linter(FORM_LINTER, "--add", "banned", "ensure", "confirm", env=env)
            result = json.loads(run_form_linter(FORM_LINTER, input_text="Ensure it works.", env=env))

            self.assertIn("ensure -> confirm", result["suggestions"])

    def test_labeled_corpus_has_no_false_results(self):
        """Keep every labeled detector case on its expected side."""
        results = json.loads(run_form_linter(CORPUS_SCORER, "--json"))
        failures = {
            detector: {"false_positives": row["false_positives"], "false_negatives": row["false_negatives"]}
            for detector, row in results.items()
            if row["false_positives"] or row["false_negatives"]
        }
        self.assertEqual(failures, {})

    def test_marketing_triad_is_advisory_only(self):
        """Keep marketing triads outside the scored total."""
        triad = json.loads(run_form_linter(FORM_LINTER, input_text="The tool is seamless, robust, and powerful."))
        plain = json.loads(run_form_linter(FORM_LINTER, input_text="The tool is seamless and robust and powerful."))

        self.assertEqual(triad["total"], plain["total"])
        self.assertEqual(triad["advisories"]["marketing_triad(advisory)"], 1)
        self.assertEqual(triad["advisories"]["messages"], ["possible marketing triad, judge it"])

    def test_new_ste_signals_are_advisory_only(self):
        """Keep contextual Issue 9 signals outside the scored total."""
        text = "1. You should analyse the result after the service has processed it.\nNOTE: Remove the cover."
        result = json.loads(run_form_linter(FORM_LINTER, "--mode", "procedure", input_text=text))

        self.assertEqual(result["total"], 0)
        self.assertEqual(result["advisories"]["american_spelling(advisory)"], 1)
        self.assertEqual(result["advisories"]["complex_verb(advisory)"], 1)
        self.assertEqual(result["advisories"]["non_imperative_step(advisory)"], 1)
        self.assertEqual(result["advisories"]["instruction_in_note(advisory)"], 1)

    def test_descriptive_mode_uses_25_word_limit(self):
        """Apply the Issue 9 descriptive sentence limit only in that mode."""
        text = "One two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty twenty-one."
        flavored = json.loads(run_form_linter(FORM_LINTER, input_text=text))
        descriptive = json.loads(run_form_linter(FORM_LINTER, "--mode", "descriptive", input_text=text))

        self.assertEqual(flavored["violations"]["long_sentence(>20w)"], 1)
        self.assertEqual(descriptive["violations"]["long_sentence(>25w)"], 0)
        self.assertEqual(descriptive["sentence_limit"], 25)

    def test_not_just_scaffold_is_scored(self):
        """Include rhetorical contrast scaffolds in the scored total."""
        result = json.loads(run_form_linter(FORM_LINTER, input_text="This is not simply a cache but a coordination layer."))

        self.assertEqual(result["violations"]["not_just_but"], 1)
        self.assertEqual(result["total"], 1)


if __name__ == "__main__":
    unittest.main()
