"""
Run all test_*.py modules in this directory and its test packages.

Usage: python tests/tests.py (using the project's Python environment)
Paths are resolved from this file, so the runner works from any directory.
Nested test directories should contain __init__.py for unittest discovery.
"""

from pathlib import Path
import sys
import unittest


def main() -> int:
    tests_dir = Path(__file__).resolve().parent
    # Use this checkout's source without requiring an editable installation.
    sys.path.insert(0, str(tests_dir.parent / "src"))
    suite = unittest.TestLoader().discover(
        start_dir=str(tests_dir),
        pattern="test_*.py",
        top_level_dir=str(tests_dir),
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
