"""The project spine for BPINFOR-132.

Course provided. Copy it into your repository in week 1 and do not fork it,
because week 10 reads what week 4 wrote and the contract is what makes that
possible.

    project/contracts.py   the artifacts that cross week boundaries
    project/trace.py       recording a run, and reading it back
    project/models.py      the local models, by role
    project/fixtures.py    replay fixtures, and the handover fallback
    project/prices.py      hosted cost estimates, clearly labeled as estimates
    project/verify.py      python -m project.verify

You are expected to read this code. It is small on purpose, and several
sessions ask you to explain a choice made in it.
"""

from .contracts import (SCHEMA_VERSION, Conditions, Finding, GoldCase,
                        GoldSet, GuardEvent, Step, Trace)
from .models import EMBED, LARGE, SMALL, VISION, preflight
from .trace import (TraceRecorder, append_trace, local_conditions,
                    read_traces, repo_root, write_json)

__all__ = [
    "SCHEMA_VERSION", "Conditions", "Finding", "GoldCase", "GoldSet",
    "GuardEvent", "Step", "Trace",
    "EMBED", "LARGE", "SMALL", "VISION", "preflight",
    "TraceRecorder", "append_trace", "local_conditions", "read_traces",
    "repo_root", "write_json",
]
