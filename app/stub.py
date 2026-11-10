"""How a stub says that it is a stub.

Every stage in `app/` starts life as a stub: a function that keeps the exact
signature of the week that will replace it, and does something honest in
the meantime. Honest means one of three things: it passes its input through
unchanged, it refuses and says so, or it falls back to the reference copy
and says so. It never pretends to have done the work.

The marker below is how the pipeline knows. It is an attribute on the
function, so it travels with the code rather than with a flag somebody has
to remember to flip. When you copy your week's file over the stub, the
marker disappears with the stub, and the next trace records that stage as
built. Every trace lists the stages that are still stubs, in
`notes["stubbed"]`, so a stubbed stage cannot be presented as a built one.
"""

from __future__ import annotations

from typing import Any, Callable


def stub(week: int, does: str) -> Callable:
    """Mark a function as a stub that week `week` replaces.

    `does` is one line saying what the stub does instead of the real work,
    for example "refuses: returns no record". It is printed by
    `python -m app.run` and recorded in the trace.
    """
    def mark(fn: Callable) -> Callable:
        fn.__stub__ = {"week": week, "does": does}
        return fn
    return mark


def stub_info(fn: Any) -> dict | None:
    """The marker, or None when the function is real code."""
    return getattr(fn, "__stub__", None)


def is_stub(fn: Any) -> bool:
    return stub_info(fn) is not None
