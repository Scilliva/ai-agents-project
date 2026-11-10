"""Stage: the human approval gate. Replaced in week 8.

Week 8 gates exactly one step, the irreversible one, with a LangGraph
`interrupt` and a checkpoint that a second process resumes. In this
application the irreversible step is submitting a case, and it reaches the
gate through one function:

    request_approval(payload: dict, unattended: bool) -> dict

`payload` has the shape of week 8's interrupt: `action`, `case_id`,
`arguments` (the exact arguments, never a summary a model wrote),
`evidence`, `degraded`, and `missing`. The return value has the shape of
week 8's resume value: `verdict` ("approve", "edit", "reject", or
"timeout"), `by`, and, for an edit, the edited `arguments`.

`unattended` is True in batch mode, which is how week 10 runs the
application. Nobody is there to answer, so your gate must return what week
8 decided an unanswered approval does after its timeout, immediately,
instead of waiting for a human who is not coming.

Until you wire yours in, the gate refuses every submission. That is the
safe default for a stub, and it means nothing irreversible can happen.

This is a stage you write rather than copy, because week 8's graph runs over
its own toy tools. Take your `submit` node from `labs/week08/starter/graph.py`
with its `interrupt` call, give it a small graph and a `SqliteSaver` of its
own, and write `request_approval` around it. Keep week 8's rule: above the
interrupt, read only.
"""

from __future__ import annotations

from .stub import stub


@stub(week=8, does="refuses: rejects every submission, nothing is submitted")
def request_approval(payload: dict, unattended: bool = False) -> dict:
    return {"verdict": "reject", "by": "stub", "arguments": {}}
