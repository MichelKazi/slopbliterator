import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FORM_LINTER = ROOT / "ste-lint.py"
WORD_LIST = ROOT / "banned-words.json"


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
    def test_demo_scores_match_baseline(self):
        """Keep the current form-linter scores stable."""
        before = json.loads(run_form_linter(FORM_LINTER, input_text=(ROOT / "demo/before.md").read_text()))
        after = json.loads(run_form_linter(FORM_LINTER, input_text=(ROOT / "demo/after.md").read_text()))

        self.assertEqual(before["total_per100w"], 18.39)
        self.assertEqual(after["total_per100w"], 0.0)

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


if __name__ == "__main__":
    unittest.main()
