"""Block 2's demonstration: the protocol core, at the wire.

    python 02_stateless.py

One raw HTTP request, with no SDK client in the way, sent twice to the legacy
Streamable HTTP transport: once with stateless transport enabled and once
with session transport enabled. In mcp==2.0.0rc1, a request declaring
protocol 2026-07-28 uses the modern stateless handler regardless of the
`stateless_http` setting, so it cannot distinguish that transport setting.

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


# The identical legacy-era tools/list request is used in both runs. It has no
# initialize handshake or session id, so the session transport must reject it
# while the stateless transport can serve it. A 2026-07-28 request cannot
# demonstrate this flag in mcp==2.0.0rc1: modern requests bypass the legacy
# session manager and are stateless by construction.
RAW_REQUEST = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {},
}


def raw_post(port: int, body: dict) -> tuple[int, dict[str, str], str]:
    """One HTTP request. No SDK, because the SDK is what hides the headers."""
    # No protocol-version header routes this legacy request to the SDK's
    # Streamable HTTP session manager in both modes.
    headers = {"Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/mcp",
        data=json.dumps(body).encode(),
        headers=headers,
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
        status, headers, body = raw_post(port, RAW_REQUEST)
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

    # Three checks. The third is the one that matters.
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
    checks = {
        "stateless request answered": stateless["status"] == 200
        and stateless["answered"],
        "stateless response has no session id": stateless["session_id"] is None,
        "same request rejected in session mode": session["status"] == 400
        and session["session_id"] is not None
        and "Missing session ID" in session["body"],
    }
    print()
    for name, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    mp.set_start_method("spawn")
    raise SystemExit(main())
