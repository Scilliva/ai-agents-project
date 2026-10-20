# Week 6 practical: memory, a stateless MCP server, and an A2A channel

BPINFOR-132, Designing, Verifying, and Shipping AI Agents.
Duration: 2 teaching units, 90 minutes. Bring a laptop.

## What your system gains this week

Increment six, and two limitations from week 5 removed.

**Every run started from nothing.** Today the agent remembers across runs.

**Its tools lived in the same process.** Today they are behind an HTTP
boundary that another process, in another language, on another machine,
could sit on the other side of.

New in the repository: a memory store, a stateless MCP server, and a case
handle that is the week's central idea.

## Why this session exists

The lecture said that statelessness relocates state rather than abolishing
it, and that the answer is an explicit handle the model can carry. Block 1
builds the store the handle points into. Block 2 mints one, and then proves
at the wire that the protocol really is carrying nothing on your behalf.

Everything you touch that depends on the protocol gets a date in a comment.
MCP runs a twelve month deprecation policy and rewrote its core eighteen
months after launch, so a file without a revision date is a file nobody can
safely re-check.

## Learning outcomes exercised

Outcome 2 (patterns and their trade-offs), outcome 7 (an application with
tool use and memory), outcome 12 (justifying trade-offs).

## Before you arrive

Read ADP-Gulli chapters 8 to 10 and chapter 15, and the MCP specification at
revision 2026-07-28. Note that MAS-Dibia chapter 12 describes the earlier
session-based model, so it is background rather than the current reference.

Install the one new dependency, and note the flag:

```bash
pip install --pre "mcp==2.0.0rc1"
```

The stable v1 line has no `MCPServer` class, so an unpinned install resolves
to something that cannot run `mcp_server.py`. The error is an `ImportError`
on the first line and the starter says so.

## Timing

| Time | Block | What you do |
|-|-|-|
| 0 to 10 | Setup | Install with `--pre`, read `memory.py` top to bottom |
| 10 to 45 | Memory | TODO 1 to 3: write, search, forget, and what k costs |
| 45 to 77 | The wire | TODO 4 to 7: the server, the handle, and the protocol at the wire |
| 77 to 85 | A2A | Watch the demonstration, answer five questions |
| 85 to 90 | Close | Commit, push, write the numbers into `DECISIONS.md` |

The ordering is deliberate and not negotiable. Block 2 exposes the store
that block 1 builds. Skipping ahead to the protocol work leaves nothing to
expose.

## Block 1, memory that survives (35 minutes)

TODO 1 to 3 in `memory.py`. Read the file top to bottom before writing
anything: the record shape at the top answers half the questions you are
about to ask.

Three decisions the markers deliberately do not make for you, and all three
go in `DECISIONS.md`:

- **What a handle looks like.** A sequential `fact-0007` tells anyone who
  sees it how many facts exist and lets them guess `fact-0006`. Week 12
  attacks exactly this.
- **What a conflicting write does.** Keep both and something has to cope
  with two contradictory facts. Overwrite and you lose what changed.
- **How long a record lives.** Nothing expires by default, which is the
  wrong answer for a service holding residents' data.

`search` is scoped to one subject before anything is scored. That boundary
is code rather than a sentence asking the model to be careful, and it is the
difference between a design and a hope.

**Checkpoint 1.** The items in `checklist.md`.

## Block 2, the wire (32 minutes)

TODO 4 and 5 in `mcp_server.py`, TODO 6 in `01_mcp_client.py`, TODO 7 in
`02_stateless.py`.

`open_case` mints a handle and later calls take it as an ordinary argument.
That is the lecture's claim made executable: the protocol carries no
session, so the state has a name the model can see.

**Then prove it, and be careful how.** Running two servers and showing that
a handle resolves on both is *not* a proof. That demonstration passes
identically with statelessness switched off, because the state is on disk
and each call opens its own connection. It shows that a file is a file.

`02_stateless.py` sends one raw HTTP request, with no SDK client in the way,
to the same server in both modes. The reference result:

| server mode | status | `Mcp-Session-Id` | answered |
|-----|-|-|-|
| `stateless_http=True` | 200 | none | yes |
| `stateless_http=False` | 400 | present | no, "Missing session ID" |

Identical bytes. One server answers them, the other refuses them, and the
refusal names the exact thing the revision removed. **A demonstration that
passes with the feature switched off is not a demonstration.**

**Checkpoint 2.** Be ready to quote the error.

## Block 3, A2A, demonstrated (8 minutes)

`03_a2a.py` is complete and has no markers. Run it, read it, and answer five
questions. Building the channel yourself is the take-home, and it is
assessed with the project exactly as the session work is.

This is a scheduling decision rather than a claim about A2A: ninety minutes
does not hold three build blocks.

## What goes into DECISIONS.md today

Six entries. Template in `starter/DECISIONS_week06_section.md`.

1. Your handle format, and what a guessable one would expose.
2. Your conflict policy and your retention policy, each with a reason.
3. What `k` costs in tokens per call, and what happens at four hundred facts.
4. The memory off against memory on comparison: tokens and turns for both.
5. The stateless result: both statuses, both headers, and the error quoted.
6. What `forget` does not reach, and why that matters.

## Homework

- Build the A2A channel yourself from the marked sections.
- Add an authorization check on the handle: today anyone holding it can read
  the case. Week 12 will attack that.
- `python -m project.verify` passing.

## If you finish early

- Put the server back in session mode and rerun `02_stateless.py`. Watch the
  third check fail. That is what a demonstration is supposed to do.
- Ask what happens to your store when two server instances write at the same
  moment. The answer is not reassuring, and naming it is worth more than
  fixing it today.

## Reference solution

In `solution/`, published after the session. The written answer to TODO 7 is
at the bottom of `02_stateless.py` and it is the part worth reading.
