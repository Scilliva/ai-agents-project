"""Run every test in tests/. Exit code 0 means everything passed.

    python run_tests.py

Standard library only, so the agent's run_tests tool needs no dependencies.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    suite = unittest.TestLoader().discover(
        start_dir=os.path.join(HERE, "tests"), top_level_dir=HERE)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"SUMMARY run={result.testsRun} "
          f"failures={len(result.failures)} errors={len(result.errors)}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
