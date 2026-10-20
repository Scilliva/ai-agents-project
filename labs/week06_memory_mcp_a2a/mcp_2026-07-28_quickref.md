# MCP 2026-07-28, one page

Model Context Protocol, specification revision **2026-07-28**, released
28 July 2026.

**This page was written on 4 August 2026 and it will go stale.** MCP runs a
formal deprecation policy with a twelve-month minimum window, which means a
revision can be superseded while the old one still works. Before each edition
of this course, and before each release of your own project, re-read the
changelog and update this page. An undated claim about a living standard is an
incomplete claim, and it is treated as one in the project report and in the
exam.

Sources: the specification at `modelcontextprotocol.io/specification/2026-07-28`,
its changelog, and the release post on `blog.modelcontextprotocol.io`.

## The one-sentence version

The protocol core moved from a stateful, bidirectional design to a stateless
request and response one, so an MCP server is now an ordinary HTTP workload
that scales behind a plain load balancer.

## What went away

| Removed | Was | Now |
| `initialize` and `initialized` | A handshake opening every connection | Nothing. Every request is self-describing. |
| `Mcp-Session-Id` header | Tied every later request to one session | Gone. No session affinity, no shared session store. |
| Server-to-client requests | `elicitation/create`, `sampling/createMessage`, `roots/list` over a held-open stream | Multi Round-Trip Requests (see below) |
| Standalone GET change stream | The old notification channel | One `subscriptions/listen` stream, opted into per notification type |
| `ping` | A liveness call | Removed outright |

## What a request looks like

```http
POST /mcp HTTP/1.1
MCP-Protocol-Version: 2026-07-28
Mcp-Method: tools/call
Mcp-Name: search

{"jsonrpc":"2.0","id":1,"method":"tools/call",
 "params":{"name":"search","arguments":{"q":"otters"},
 "_meta":{"io.modelcontextprotocol/clientInfo":
          {"name":"my-app","version":"1.0"}}}}
```

Protocol version, client identity, and client capabilities travel in `_meta` on
every request. A client that wants capabilities up front can call
`server/discover`, which is optional.

## The four changes worth knowing

**Statelessness relocates state.** A stateless protocol does not make your
application stateless. If a tool needs to carry state across calls, it mints an
explicit handle, returns it, and the model passes it back as an ordinary
argument. The state becomes something the model can see, your trace can assert
on, and a red team can attack, which is better than state hidden in a transport.

**Multi Round-Trip Requests (MRTR).** When a tool needs a confirmation or a
missing parameter mid-call, the server returns `resultType: "input_required"`
with what it needs and an opaque request state token. The client obtains the
answers and calls the same tool again with them attached in `inputResponses`.
Every leg is a client-to-server request, which is what makes it survive a load
balancer. This is the protocol form of the human-in-the-loop pattern developed
in week 8.

**Header-based routing.** Streamable HTTP requests carry `Mcp-Method` and, for
tool calls, `Mcp-Name`. A gateway, rate limiter, or web application firewall can
route, meter, and authorise on headers without parsing the JSON body. Security
caveat: the header asserts what the body claims to be, so a server must validate
that the two agree. Returns in week 11 as a gateway concern.

**Cacheable list results.** `tools/list`, `prompts/list`, `resources/list`, and
`resources/read` carry `ttlMs` and `cacheScope`, with deterministic ordering.
The direct win is fewer round trips. The larger win is upstream: the tool
catalog is part of your prompt, so a stable, deterministically ordered
catalog keeps the provider's prompt cache warm. Treat a cache hint as a cost
argument, never as a correctness argument.

## Authorisation hardening

- Authorisation servers should return the `iss` parameter per RFC 9207, and
  clients must validate it before redeeming a code. This closes an
  authorisation-server mix-up hole.
- Client credentials are bound to the issuer that minted them. No reuse across
  authorisation servers.
- Dynamic Client Registration (DCR) is formally deprecated in favour of Client
  ID Metadata Documents (CIMD). DCR still works, for now.
- Clients set `application_type` during DCR, so authorisation servers stop
  rejecting `localhost` redirects for desktop and command-line applications.

Week 12 uses this section as a worked example of a protocol hardening itself in
response to deployment experience.

## Deprecated, with at least twelve months of life left

- Roots, Sampling, and Logging. They still work. Do not adopt them in new code.
- The legacy HTTP with Server-Sent Events transport, on the same offramp.
- Dynamic Client Registration, as above.

Expect a deprecation warning on your first `ctx.info(...)` call after upgrading.

## Extensions

Tasks moved out of the experimental core into the `io.modelcontextprotocol/tasks`
extension, with a poll-based `tasks/get` and a new `tasks/update`. MCP Apps and
Enterprise Managed Authorization (EMA) are extensions too. The extensions
framework itself was formalised in this revision.

## Python SDK notes

The version 2 line of the official Python SDK speaks this revision. As of late
July 2026 it was a pre-release, so pin an exact version.

| Version 1 | Version 2 |
| `FastMCP` | `MCPServer` |
| `mcp.server.fastmcp.*` | `mcp.server.mcpserver.*` |
| transport options on the constructor | transport options on `run()` and the app builders |
| camelCase attributes | snake_case attributes (`result.is_error`, `tool.input_schema`) |
| transport, then `ClientSession`, then `initialize()` | one `Client` object |
| wire types inside `mcp` | wire types in `mcp-types`, imported as `mcp_types` |

One version 2 server serves both protocol eras from the same
`streamable_http_app()`, so a 2025-era client sending `initialize` and a
2026-era client sending a self-describing request are both answered. OpenTelemetry
middleware is enabled by default, which is where the tracing material of week 10
picks this up.

## Where the textbooks stand

ADP-Gulli chapter 10 is a good introduction to MCP as a pattern and predates
this revision. MAS-Dibia chapter 12 describes the protocol landscape well and
describes the session-based model, so its handshake and session material is
history. Read both for the shape of the problem. Read the specification for the
wire.

## Verified against the SDK, 2026-08-10

Everything above was checked against `mcp==2.0.0rc1` rather than taken from
the specification alone. `mcp_smoke_test.py` reproduces it.

Three things the specification does not tell you and the SDK does:

- Install needs a pre-release flag: `pip install --pre "mcp==2.0.0rc1"`.
  The stable v1 line has no `MCPServer` and an unpinned install fails on the
  first import.
- Host and port are keyword arguments to `run_streamable_http_async`, not
  fields on `app.settings`. Assigning `app.settings.port` raises
  `ValueError: "Settings" object has no field "port"`.
- **`stateless_http=True` is not the default.** Omit it and the server runs
  the old session-based model while your code claims otherwise. The
  difference is visible at the wire and `02_stateless.py` measures it:
  stateless returns 200 with no session header, session mode returns 400 and
  `Bad Request: Missing session ID` to the identical request.
