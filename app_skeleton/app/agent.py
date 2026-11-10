"""Stage: the agent loop and its caps. Replaced in week 4.

Until you wire yours in, the agent refuses: it answers that it cannot
answer yet and points to the help desk, which is exactly what your capped
loop says when a cap fires.

To replace it, copy your `labs/week04/starter/agent.py` over this file and
make two edits.

1. Its sibling imports become relative:

       from handbook import INJECTION_MARKER    ->  from .handbook import ...
       from tools import ...                    ->  from .tools import ...

2. `run_task` records its own trace. Inside the application the pipeline
   records one trace per request, so pass `persist=False` to the
   `rec.finish(...)` call at the end of `run_task`. Otherwise every request
   writes two traces, and week 10 counts each run twice.

Keep these names and signatures, because `pipeline.py` calls them:

    Run                               answer, steps, tool_calls, tokens,
                                      cap_fired, tool_errors, saw_injection
    SYSTEM: str
    run_task(client, task, model=LARGE.name, max_steps=6, stall_limit=2,
             system=SYSTEM, week=4) -> Run

`task` needs three attributes: `id`, `lang`, and `question`. The pipeline
passes a `pipeline.Request`, which has all three.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from project.models import LARGE

from .stub import stub

SYSTEM = ""


@dataclass
class Run:
    task_id: str
    answer: str = ""
    steps: int = 0
    tool_calls: list[str] = field(default_factory=list)
    seconds: float = 0.0
    tokens: int = 0
    cap_fired: str | None = None
    saw_injection: bool = False
    tool_errors: int = 0

    @property
    def stopped_cleanly(self) -> bool:
        return self.cap_fired is None


@stub(week=4, does="refuses: says it cannot answer yet, calls no tool")
def run_task(client, task, model: str = LARGE.name,
             max_steps: int = 6, stall_limit: int = 2,
             system: str = SYSTEM, week: int = 4) -> Run:
    return Run(task_id=task.id, cap_fired="stub",
               answer=("I cannot answer questions yet. Please telephone the "
                       "help desk on 4796-2222."))
