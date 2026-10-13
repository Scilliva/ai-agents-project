"""The toy repository, its tools, and the verifier. Given complete.

Nothing to complete here. Read `apply_fix` and `run_tests` before you start,
because between them they decide what "done" means today.

The domain is code for one reason: it is the only agentic task in this
course with a free, fast, deterministic verifier. The tests pass or they do
not, so nobody argues about answer quality today. Every other domain in this
course has to build a judge, and that is weeks 10 to 12.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent / "toyrepo"


@dataclass
class Work:
    """One scratch copy of the repository. The agent never sees the original.

    Every run gets a fresh copy. If you edit toyrepo/ directly, your next run
    starts from a repository that is already fixed and every number after
    that is meaningless.
    """

    root: Path

    @classmethod
    def fresh(cls) -> "Work":
        tmp = Path(tempfile.mkdtemp(prefix="week05_"))
        shutil.copytree(SOURCE, tmp / "repo")
        return cls(root=tmp / "repo")

    def cleanup(self) -> None:
        shutil.rmtree(self.root.parent, ignore_errors=True)

    def read(self, path: str) -> str:
        target = self.root / path
        return (target.read_text(encoding="utf-8") if target.exists()
                else f"ERROR: no such file: {path}")

    def files(self) -> list[str]:
        return sorted(str(p.relative_to(self.root))
                      for p in self.root.rglob("*.py")
                      if "__pycache__" not in str(p))


@dataclass
class TestResult:
    passed: bool
    ran: int
    failures: int
    errors: int
    output: str

    @classmethod
    def parse(cls, text: str) -> "TestResult":
        line = next((ln for ln in text.splitlines()
                     if ln.startswith("SUMMARY")), "")
        nums = {k: 0 for k in ("run", "failures", "errors")}
        for part in line.replace("SUMMARY", "").split():
            if "=" in part:
                k, _, v = part.partition("=")
                if k in nums and v.isdigit():
                    nums[k] = int(v)
        return cls(passed=bool(line) and nums["failures"] == 0
                   and nums["errors"] == 0,
                   ran=nums["run"], failures=nums["failures"],
                   errors=nums["errors"], output=text[-1200:])


def run_tests(work: Work) -> TestResult:
    """The verifier. Free, fast, and not open to interpretation."""
    proc = subprocess.run([sys.executable, "run_tests.py"], cwd=work.root,
                          capture_output=True, text=True, timeout=90)
    return TestResult.parse(proc.stdout + proc.stderr)


def apply_fix(work: Work, path: str, old_line: str, new_line: str) -> str:
    """Apply one proposed line replacement, or refuse and say why.

    Four refusals, and each one is a control rather than a convenience.

      * a test file is never editable, so the agent cannot make the suite
        green by deleting the test that fails
      * the file has to exist
      * the old text has to appear exactly once, so an ambiguous edit is
        rejected rather than guessed at
      * the old text has to appear at all, which catches the model
        hallucinating a line that is not in the file

    Note who is enforcing these. Not the model, and not its instructions.
    This function. That distinction is the whole of week 4's block 3 and it
    returns in week 11 as the difference between a guardrail and a request.
    """
    if path.startswith("tests/") or "/tests/" in path or path.endswith(
            "run_tests.py"):
        return "REFUSED: test files are not editable."
    target = work.root / path
    if not target.exists():
        return f"REFUSED: no such file: {path}"
    text = target.read_text(encoding="utf-8")
    if old_line not in text:
        return ("REFUSED: that line does not appear in the file. It has to "
                "be copied character for character.")
    if text.count(old_line) > 1:
        return (f"REFUSED: that line appears {text.count(old_line)} times, "
                f"so the edit is ambiguous.")
    target.write_text(text.replace(old_line, new_line), encoding="utf-8")
    return "applied"


def diff_summary(work: Work, path: str, old_line: str,
                 new_line: str) -> str:
    """What the reviewer is shown. The change, and nothing else."""
    return (f"--- {path}\n- {old_line.strip()}\n+ {new_line.strip()}")
