# Week 3 checklist

## Checkpoint 1, control and treatment

Six items. Do not move to block 3 until all six are true.

- [ ] The five route definitions written down in one sentence each, **before**
      any prompt was written, each defined by what the help desk must do
      rather than by how the message sounds
- [ ] The monolith control running over all twenty four queries, and you can
      say in one sentence why it is a fair opponent rather than a straw man
- [ ] The router running over the same twenty four, with route, confidence,
      and evidence logged for every one
- [ ] A confidence threshold chosen **after** printing the distribution, not
      before. You can say what fraction of calls fall below it.
- [ ] The evidence span checked by substring search against the query, not
      by eye
- [ ] A safe default chosen, with one sentence on why that route and not
      another. The question to answer is which specialist does the least on
      the sender's behalf.

**If your threshold fires on zero queries**, that is a finding, not a
mistake. Write down what it tells you about that model's confidence before
you change the number.

## Checkpoint 2, was the router worth it

Six items. Be ready to say your numbers out loud, per route, as counts.

- [ ] Per-route accuracy reported as counts, and the confusion pairs named
      **with their direction**
- [ ] The route carrying most of the error identified, and one sentence on
      whether the fix is a definition or a prompt
- [ ] Routing overhead computed: the classifying call as a share of the
      routed system's total tokens. Predict it before you look.
- [ ] The four ambiguous queries discussed, with your convention written
      down and defended
- [ ] One sentence naming something a specialist can be forbidden to do that
      the monolith cannot be given
- [ ] Both scoreboards saved to disk, and `artifacts/goldset.json` now
      holding thirty four cases

## Before you leave

- [ ] Code committed and pushed
- [ ] `python -m project.verify` passes
- [ ] `DECISIONS.md` has all six entries, every number carrying its model
      name and run date
- [ ] The stretch variant attempted, or explicitly deferred with a reason

## Homework, before week 4

- [ ] The comparison run live, if you only used the recording
- [ ] Your week 2 extractor wired in behind the `request` route, so that
      route produces a validated record rather than prose. This is the first
      place the two weeks become one system.
- [ ] One sentence in `DECISIONS.md` naming the route whose definition you
      would rewrite first, and what you expect it to move

## What "done" means here

The deliverable is the comparison and the diagnosis, not the router. A
student who finishes with a working router and no monolith control has not
done the exercise. A student whose router lost to the monolith, who can name
the confusion pair, say which definition caused it, and price the routing
call, has done it completely.

A negative result reported honestly scores above a win claimed on twenty
four queries.
