"""Stage: the route definitions and the specialist prompts. Replaced in week 3.

Copy your `labs/week03/starter/routes.py` over this file, together with
`router.py`. `pipeline.py` reads two names from it:

    ROUTES: tuple[str, ...]          the five route names
    SPECIALISTS: dict[str, str]      one system prompt per route

Nothing here is called while the router is a stub, because the stub router
sends every message down the answer path.
"""

from __future__ import annotations

ROUTES = ("request", "info", "status", "complaint", "other")

SPECIALISTS: dict[str, str] = {route: "" for route in ROUTES}
