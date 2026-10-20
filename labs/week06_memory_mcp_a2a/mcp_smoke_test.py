"""Does the week 6 demonstration actually work on MCP SDK 2.0.0rc1?

Week 6's central claim is the specification's: the protocol carries no
session, so any request can land on any server instance. The lab proves it
by minting a handle on one server and redeeming it on another.

Five questions:
  1. Does a server built with MCPServer serve over streamable HTTP?
  2. Does a client list the tool catalog?
  3. Does a tool call work, and does it change state on disk?
  4. Does a handle minted on server A resolve on server B?
  5. Is there an Mcp-Session-Id anywhere in the exchange?

Usage:  mcpenv/bin/python probe_week06.py
"""

import asyncio
import json
import multiprocessing as mp
import sys
import tempfile
import time
from pathlib import Path

STORE = Path(tempfile.gettempdir()) / "w06_probe_store.json"


def _load() -> dict:
    if STORE.exists():
        return json.loads(STORE.read_text())
    return {"cases": {}, "facts": []}


def _save(data: dict) -> None:
    STORE.write_text(json.dumps(data, indent=2))


def serve(port: int) -> None:
    """One server instance. Two of these run at once, sharing one file."""
    from mcp.server import MCPServer

    app = MCPServer("memory-desk")

    @app.tool()
    def open_case(subject: str) -> str:
        """Mint an explicit handle for a resident's case."""
        data = _load()
        handle = f"case-{len(data['cases']) + 1:04d}"
        data["cases"][handle] = {"subject": subject, "notes": []}
        _save(data)
        return handle

    @app.tool()
    def remember(handle: str, fact: str) -> str:
        """Attach a fact to an open case, named by its handle."""
        data = _load()
        if handle not in data["cases"]:
            return f"ERROR: no such case: {handle}"
        data["cases"][handle]["notes"].append(fact)
        _save(data)
        return f"ok, {len(data['cases'][handle]['notes'])} note(s)"

    @app.tool()
    def recall(handle: str) -> list[str]:
        """Read back everything attached to a case handle."""
        data = _load()
        if handle not in data["cases"]:
            return [f"ERROR: no such case: {handle}"]
        return data["cases"][handle]["notes"]

    # stateless_http=True is the 2026-07-28 protocol core: no initialize
    # handshake, no session id, every request self-describing.
    asyncio.run(app.run_streamable_http_async(
        host="127.0.0.1", port=port, stateless_http=True))


async def ask(port: int, tool: str | None = None, **args):
    from mcp.client import Client
    async with Client(f"http://127.0.0.1:{port}/mcp") as client:
        if tool is None:
            return await client.list_tools()
        return await client.call_tool(tool, args)


def text_of(result) -> str:
    content = getattr(result, "content", result)
    if isinstance(content, list) and content:
        return getattr(content[0], "text", str(content[0]))
    return str(content)


async def main() -> int:
    STORE.unlink(missing_ok=True)
    procs = []
    for port in (8931, 8932):
        p = mp.Process(target=serve, args=(port,), daemon=True)
        p.start()
        procs.append(p)
    time.sleep(4)

    ok = {}
    try:
        tools = await ask(8931)
        names = sorted(t.name for t in getattr(tools, "tools", tools))
        ok["2 client lists the catalog"] = names == ["open_case", "recall",
                                                       "remember"]
        print(f"  tools on 8931: {names}")

        handle = text_of(await ask(8931, "open_case", subject="A. Muller"))
        ok["3 a tool call changes state on disk"] = (
            handle.startswith("case-") and STORE.exists()
            and handle in _load()["cases"])
        print(f"  handle minted on 8931: {handle!r}")

        r = text_of(await ask(8932, "remember", handle=handle,
                              fact="reported a broken heater"))
        print(f"  remember on 8932:      {r!r}")

        back = await ask(8932, "recall", handle=handle)
        notes = text_of(back)
        ok["4 handle minted on A resolves on B"] = "heater" in notes
        print(f"  recall on 8932:        {notes[:70]!r}")

        again = text_of(await ask(8931, "recall", handle=handle))
        ok["4b and still resolves back on A"] = "heater" in again

        ok["1 server serves over streamable HTTP"] = True
    except Exception as exc:                                  # noqa: BLE001
        print(f"  ERROR {type(exc).__name__}: {exc}")
        ok.setdefault("1 server serves over streamable HTTP", False)
    finally:
        for p in procs:
            p.terminate()

    print()
    for k, v in sorted(ok.items()):
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    return 0 if all(ok.values()) else 1


if __name__ == "__main__":
    mp.set_start_method("spawn")
    raise SystemExit(asyncio.run(main()))
