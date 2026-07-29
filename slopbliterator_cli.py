"""Console entry points for the repository scripts."""

from pathlib import Path
import runpy


def slop_lint():
    """Run the form linter."""
    runpy.run_path(Path(__file__).with_name("ste-lint.py"), run_name="__main__")


def slop_substance():
    """Run the substance linter."""
    runpy.run_path(Path(__file__).with_name("substance-lint.py"), run_name="__main__")
