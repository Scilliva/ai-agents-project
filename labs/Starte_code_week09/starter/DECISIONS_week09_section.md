# Week 9, the vision step

Copy this into your project `DECISIONS.md` and fill it in. In week 13 this
becomes a section of your report that you do not have to write.

Every number below needs its conditions beside it: the model, the variant,
the date, and whether it was live or replayed. A vision number without its
variant is not evidence, because the same pipeline gives a different answer
on the same document at 40 percent scale.

## Conditions

- Model and version:
- Context length (`OLLAMA_CONTEXT_LENGTH`):
- Temperature:
- Run date:
- Live or `--replay`:

## The architecture, and why

We read the six fields in ______ call(s) per document.

Our reason, in one sentence, and it must be a measured one:

The wall clock and largest output token count we measured for each
architecture:

| architecture | total wall clock | largest output tokens | guard failures |
| grouped |  |  |  |
| naive, one call |  |  |  |

If both architectures produced the same outcomes, say so plainly and say
what you concluded from it. "It worked when we tested it" is the beginning
of the argument, not the end.

## The guard

The response shapes our `guard` refuses, and how each one was provoked:

| refused shape | how we triggered it | what a naive check would have done |
|  |  |  |
|  |  |  |
|  |  |  |

The one that would have reached our database if `guard` were not there:

## The checks

The four checks we built, and what each one is actually able to catch:

| check | catches | cannot catch |
|  |  |  |

The wrong extraction our checks cannot catch, stated concretely with
numbers:

What we would have to add to catch it, and what that would cost:

## Block 1 result

| outcome | count |
| correct |  |
| false alarm |  |
| caught |  |
| WRONG |  |
| refused |  |

Why a run of five correct and zero fired is not yet evidence that the checks
work:

## The operating limit

The sweep table, with the variant names as we ran them:

| variant | correct | caught | WRONG | refused |
|  |  |  |  |  |

The variants that changed nothing, and why that is a result:

The first document to fail, and what is different about it:

The one sentence we would put in our documentation about the operating
limit of this pipeline, naming the worst document rather than an average:

Whether the model invented a value or refused to give one, and the two
conditions in our setup that we think are responsible:

## Untrusted input

The sentence on INV-005 that is addressed to the assistant, quoted:

What the model triage route decided for INV-005, and the reason it gave:

The line in `code_triage` that makes this attack impossible, quoted:

Why the code route approving INV-005 is not the injection succeeding:

What we would have to change for the injection to work against the code
route:

## Cost and latency

| step | calls per document | median seconds | notes |
| extraction |  |  |  |
| checks |  | 0 | no model call |
| triage |  |  |  |

The cheapest thing we could do to halve the latency, and what it would cost
in accuracy:

## What we would do differently with a hosted frontier model

One paragraph. Name what you expect to change and what you expect to stay
the same, and mark clearly which parts are measured and which are guesses.
