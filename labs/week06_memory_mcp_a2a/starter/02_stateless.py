"""Block 2's demonstration: the protocol core, at the wire. TODO 7.

    python 02_stateless.py

One raw HTTP request, with no SDK client in the way, sent twice: once to a
server running the 2026-07-28 stateless core, and once to the same server
put back into session mode. Same bytes, same tools, same everything else.

This replaces an earlier version of this demonstration that started two
servers, alternated a client between them, and showed that a case handle
still resolved. That version passed identically in both modes, because the
state was in a shared file and the client opened a fresh connection per
call. It proved that a file is a file.

The bar for a demonstration is that it FAILS when the thing being
demonstrated is switched off. This one does.
"""

from __future__ import annotations

import asyncio
import json
import multiprocessing as mp
import time
import urllib.error
import urllib.request

PORT_STATELESS = 8941
PORT_SESSION = 8942


def serve(port: int, stateless: bool) -> None:
    """One server. The only difference between the two runs is `stateless`."""
    from mcp.server import MCPServer

    app = MCPServer("memory-desk")

    @app.tool()
    def recall(handle: str) -> list[str]:
        """Read back everything attached to a case handle."""
        return [f"notes for {handle}"]

    asyncio.run(app.run_streamable_http_async(
        host="127.0.0.1", port=port, stateless_http=stateless))


# The request that carries its own context. Note what is in `params`: the
# protocol version, who the client is, and what it can do. Under the old
# protocol none of this was here, because it had been established once
# during an `initialize` handshake and then remembered by the server. Moving
# it into every request is exactly what "self-describing" means, and it is
# what makes the request routable to any instance.
# TODO 7a. Build the self-describing request.
#
# A `tools/list` call, JSON-RPC 2.0. The interesting part is `params`: it has
# to carry its own protocolVersion, clientInfo, and capabilities, because
# under this revision there is no handshake that established them earlier.
# Look at the specification for the exact field names before you guess.
SELF_DESCRIBING = {}   # TODO 7a


def raw_post(port: int, body: dict) -> tuple[int, dict[str, str], str]:
    """One HTTP request. No SDK, because the SDK is what hides the headers."""
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/mcp",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream"},
        method="POST")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, dict(response.headers), \
                response.read().decode()[:400]
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read().decode()[:400]


def ask(stateless: bool, port: int) -> dict:
    process = mp.Process(target=serve, args=(port, stateless), daemon=True)
    process.start()
    time.sleep(4)
    try:
        status, headers, body = raw_post(port, SELF_DESCRIBING)
        lower = {k.lower(): v for k, v in headers.items()}
        return {"stateless": stateless, "status": status,
                "session_id": lower.get("mcp-session-id"),
                "answered": '"tools"' in body, "body": body}
    finally:
        process.terminate()


def main() -> int:
    rows = [ask(True, PORT_STATELESS), ask(False, PORT_SESSION)]

    print(f"\n{'server mode':<24}{'status':>8}{'Mcp-Session-Id':>36}"
          f"{'answered':>10}")
    print("-" * 78)
    for row in rows:
        mode = ("stateless_http=True" if row["stateless"]
                else "stateless_http=False")
        print(f"{mode:<24}{row['status']:>8}"
              f"{str(row['session_id'])[:34]:>36}{str(row['answered']):>10}")
    print()
    for row in rows:
        print(f"  {'stateless' if row['stateless'] else 'session  '} body: "
              f"{row['body'][:110]}")

    # TODO 7b. Three checks. The third is the one that matters.
    #
    # A demonstration is only worth running if it FAILS when the thing being
    # demonstrated is switched off. An earlier version of this block started
    # two servers and showed a case handle resolving on both; it passed
    # identically in session mode, so it demonstrated nothing.
    #
    # So: assert that the stateless server answers, that it issues no
    # session id, AND that the identical request is refused by the server in
    # session mode. If your third check passes in both modes, you have
    # rebuilt the broken version.
    stateless, session = rows
    checks = {}   # TODO 7b
    print()
    for name, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    mp.set_start_method("spawn")
    raise SystemExit(main())
