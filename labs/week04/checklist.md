# Week 4 checklist

## Checkpoint 1, the loop runs and stops

Six items. Do not move to block 2 until all six are true.

- [ ] Both tool schemas convert and are accepted by the endpoint, and each
      description says what it returns, when **not** to use it, and what an
      empty result means
- [ ] The loop runs end to end on at least one task, with the answer printed
- [ ] All three caps implemented: step limit, budget, and a no-progress check
- [ ] A cap firing returns a partial answer naming what happened, never an
      empty string and never a traceback
- [ ] A per-task trace recorded: step count, the tool sequence, and which cap
      fired if any
- [ ] One tool error forced deliberately, and you have checked that the error
      text you hand the model contains no file path

## Checkpoint 2, what the traces showed

Six items. Counts and task ids, never percentages.

- [ ] Task accuracy reported as counts, with the failing task ids named
- [ ] Step distribution reported: minimum, maximum, and where the long tail
      came from
- [ ] The no-tool baseline run on the same ten tasks, so you can say what the
      tools bought
- [ ] T-08 checked: did the agent call a tool it did not need
- [ ] T-10 checked: did the agent say it could not find the answer, or invent
      one. If it invented one, quote it.
- [ ] The notice board result stated plainly: did the hostile text reach the
      model, and did the agent follow it. Two separate questions.

**If your scorer reports 10 of 10 on the recording**, it does nothing. The
reference run passes 5 of 10.

## Checkpoint 3, the defense ladder

- [ ] Your prediction written down before you ran it
- [ ] Four system prompts tried, from no defense to a determined one
- [ ] The result reported as a count out of eight, not as an impression
- [ ] One sentence in `DECISIONS.md` on what this means for weeks 11 and 12

## Before you leave

- [ ] Code committed and pushed
- [ ] `python -m project.verify` passes, gold set at 44 cases
- [ ] `DECISIONS.md` has all six entries, every number with its model and date
- [ ] Entry 6, the blast radius, is written. It is the one week 12 looks up.

## Homework, before week 5

- [ ] The full set run live, on both text models
- [ ] The no-tool baseline run
- [ ] One sentence naming the failure your scorer currently cannot detect

## What "done" means here

The deliverable is the four findings and the blast radius, not the loop. A
student whose agent passes eight tasks and who cannot say what it does with
the notice board has not done the session. A student whose agent passes four,
who can name every failure by kind and say which are bounded by architecture
rather than by the model's goodwill, has done it completely.
