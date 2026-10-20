# Week 6 checklist

## Checkpoint 1, memory that pays

Six items. All six before you open the MCP files.

- [ ] The store survives a process restart, proven by running twice and
      getting different behavior
- [ ] `write` returns a handle, and you can say what a guessable handle
      would expose
- [ ] `search` is scoped to one subject, and you have checked that another
      subject's facts do not come back
- [ ] `search` respects `k`, and you can say what `k` costs in tokens per call
- [ ] `forget` works, and you can say what it does **not** reach
- [ ] One sentence in `DECISIONS.md` on conflict handling, and one on how
      long a record lives

## Checkpoint 2, the wire

Six items. The last one is the one that matters.

- [ ] The server runs over streamable HTTP and the client prints the
      catalog it discovered
- [ ] A tool call changes `artifacts/memory_store.json`, and you watched it
      change
- [ ] `open_case` returns a handle, and a later call carrying that handle
      succeeds on a second instance
- [ ] You can say why the previous item does **not**, on its own, prove the
      protocol is stateless
- [ ] No `Mcp-Session-Id` anywhere in your own code, and a comment naming
      revision 2026-07-28 wherever you rely on it
- [ ] The identical raw request answered by the stateless server (200, no
      session header) and refused by the same server in session mode
      (400, "Missing session ID"), and you can quote the error

**If your third check in `02_stateless.py` passes in both modes**, you have
rebuilt the broken version of this demonstration. A demonstration that
passes with the feature switched off is not a demonstration.

## Checkpoint 3, delegation observed

Nothing here asks you to have built it. It asks what you saw.

- [ ] You ran the demonstration and the output is in front of you
- [ ] You can name the card field the client read, and why question two was
      never sent
- [ ] You can describe the states a task passed through, and where the
      artifact appeared
- [ ] You can say what the client did on the failed path and on the timed
      out path, and why the task id is kept
- [ ] You can say why the branch for an artifact with no text part reports a
      mismatch rather than stringifying it
- [ ] Take-home: build the channel yourself from the marked sections

## Before you leave

- [ ] Code committed and pushed
- [ ] `python -m project.verify` passes
- [ ] `DECISIONS.md` has all six entries, with the SDK version and the
      specification revision
- [ ] Every protocol comment carries revision 2026-07-28

## Homework, before week 7

- [ ] The A2A channel built from the marked sections
- [ ] An authorization check on the handle. Today anyone holding it can read
      the case, and week 12 will attack that.
- [ ] Keep your keyword `search` behind one method. Week 7 replaces its body
      with embeddings and the signature does not change.

## What "done" means here

The deliverable is the wire result and the reasoning about state, not the
server. A student whose server runs and who cannot say why the two-instance
handle demonstration proves nothing has missed the session. A student who
can quote the 400 and explain that the state became an argument rather than
disappearing has done it completely.
