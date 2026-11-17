# Week 9 checklist

Tick these as you go. The in-session list is what a demonstrator will ask
you about while walking the room.

## In session

### Block 1, extract and check (8 to 45)

- [ ] `ollama pull qwen3-vl:4b` finished, and `01_extract.py --replay` prints
      a table before you write any code
- [ ] All six images opened and looked at, including `SCREEN-01.png`
- [ ] TODO 1, `guard`, refuses all five bad responses, and you have run it
      against each one on purpose rather than assuming
- [ ] `guard` refuses the object whose every value is a blank string. That
      object parses and has all its keys, so a naive check accepts it.
- [ ] TODO 2 does not pass `think=False`. Try it once, see the blanks, and
      then take it out.
- [ ] TODO 3, four checks, and none of them calls a model
- [ ] Your checks correctly accept INV-002, which legitimately has no
      purchase order. A missing optional field is not an error.
- [ ] You worked out by hand what `1180.80 + 200.74 = 1381.54` does to your
      arithmetic check, and can say in one sentence why it passes
- [ ] `01_extract.py` runs and writes `artifacts/week09_extractions.json`
- [ ] You can say why five correct and zero fired is not yet good news

### Block 2, break it (45 to 72)

- [ ] `python 02_break.py --sweep` STARTED live at the top of the block, and
      you carried on working instead of watching it
- [ ] TODO 4a and 4b done, and `perturb.py` composes steps with `+`
- [ ] The sweep table read, with the WRONG column read first
- [ ] You can name the variants that changed nothing, and say why a flat row
      is a result rather than a bug in the harness
- [ ] You can name the one document that fails first and say what is
      different about it
- [ ] The architecture comparison run, and you can state the wall clock and
      the largest output token count for both
- [ ] You can say why "the naive version worked" is a reason to distrust it
      rather than to ship it

### Block 3, untrusted input (72 to 85)

- [ ] You have found the sentence on INV-005 that is addressed to the
      assistant, by reading the image yourself
- [ ] TODO 5 done, and you can point at the line that proves no string from
      the page reaches the decision
- [ ] `03_untrusted.py` run, and you can say what the model route did with
      INV-005 and quote the reason it gave
- [ ] You can say why the code route approving INV-005 is NOT the injection
      succeeding

### Close (85 to 90)

- [ ] `DECISIONS.md` section written, with the conditions beside every number
- [ ] Committed and pushed

## Homework

- [ ] One document of your own, photographed rather than rendered, run
      through the sweep, and where it sits relative to the five here
- [ ] `code_triage` wired to the week 8 approval gate, so a failed check
      routes to a human instead of printing a verdict
- [ ] One paragraph: what fires your gate, and why it is not model
      confidence

## The three things a demonstrator will ask

1. Show me your `guard` refusing an object whose keys are all present and
   whose values are all blank.
2. Your arithmetic check catches inconsistency. Show me a wrong extraction
   it cannot catch, and tell me what would.
3. Point at the line that makes the sentence on INV-005 unable to change
   your gate decision.
