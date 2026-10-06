# Tool schema design, one page

BPINFOR-132, week 4. Keep this open while you write your tool descriptions.

A tool schema is an interface contract with one unusual property: its only
reader is probabilistic. The name is an identifier that has to be reproduced
exactly. The input schema is a validation boundary that both your code and
the provider can enforce. The description is the only part read by a language
model rather than by a parser, which makes writing it prompt engineering
rather than documentation.

Everything you can put in the schema is machine checkable and cannot be
violated. Everything you can only say in the description is advisory. Prefer
the schema.

## The four parts of a description

Students write part one and stop. Parts two and four are where the failures
are.

| Part | What it says | The failure it prevents |
| 1. What it does | One sentence, imperative, naming the corpus or system it acts on | The model treats a handbook search as a web search |
| 2. When, and when not | Which questions it is for, and the sibling tool it is confused with | Tool confusion, and tool abuse on tasks that need no tool at all |
| 3. What it returns | The shape, the fields, and the ordering | The model cannot cite a doc_id it did not know was there |
| 4. Empty and error | What an empty result means and what to do about it | An undefined silence, which the model fills with a plausible invention |

Part four is the single highest leverage sentence in this file. "An empty
list means the handbook does not cover the question: say so plainly, name the
service to contact, and never invent a figure" is the difference between a
system that admits ignorance and one that states a fee that does not exist.

## The six decisions, from the lecture

| Decision | Options | How to choose |
| Granularity | One broad tool or several narrow ones | Narrow tools are easier to describe and easier to confuse. Start with few. |
| Arguments | Free-form string or a closed structured schema | Closed wherever the value set is known. A constraint in the schema is a bug that cannot happen. |
| Side effects | Read-only, write, or irreversible | Read-only can be retried freely. Anything irreversible needs a confirmation, and week 8 gives it a human. |
| Failure shape | Raise, or return an error the model can read | Return it. A model that sees "no such reference" can recover. A stack trace ends the turn. |
| Result size | Everything, a summary, or a handle | Results enter the context and are re-sent every step. Cap them, and return a handle for anything large. |
| Permissions | What the executor may do per call | Least privilege, per tool, enforced in your code. The model has no privileges of its own. |

## Worked example, before and after

Before, and this is what a first attempt usually looks like:

```
"description": "Searches the service database."
```

Four observed failures with that description, all of them on the week 4 task
set: the model sends the user's full question as the query and retrieves the
wrong document, it searches for "26 times 8.50" instead of using the
calculator, it searches the handbook for a translation task, and on a query
with no match it answers with an invented fee.

After, with each clause doing one job:

```
"description": (
    "Search the Remerbaach service handbook for opening hours, fees, "
    "forms, procedures, and contact details. "
    "Send KEYWORDS, not a full sentence: 'waste collection fee 240 litre' "
    "works, 'How much does a 240 litre bin cost per year?' does not. "
    "Use it for any factual question about a commune service. "
    "Do NOT use it for arithmetic, for translation, or to look up a person "
    "or an individual reference number. "
    "Returns a list of at most top_k passages, each with a doc_id, a title, "
    "and a verbatim snippet, best match first. "
    "An empty list means the handbook does not cover the question: say so "
    "plainly, name the service to contact, and never invent a figure."
)
```

## Argument design

Put it in the schema when you can.

```python
"top_k": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3}
```

That is better than "top_k should be between 1 and 5" in the description,
because a request for fifty is now impossible to construct rather than merely
discouraged. The same argument applies to enumerations, string patterns, and
required fields. Every constraint you move from prose into the schema is a
class of wrong call that stops existing.

Where a value set is known and small, use an enumeration rather than a
string. Where a format matters, give one worked example inside the argument
description. "'26 * 8.50 + 24.00'" prevents more failed calls than three
sentences of grammar.

## The executor is where the privileges are

The model emits a name and an arguments object. Your code decides whether to
run it. Four responsibilities, in order:

1. look the name up, and treat a miss as a recoverable error result naming
   the tools that do exist
2. execute inside a try that catches `Exception`, not only the errors you
   expected
3. write the error text for the model: what went wrong, and what a different
   call would have to look like. Never a stack trace: it is long, it is
   expensive, it leaks paths and versions, and it cannot be acted on.
4. cap the size of the result, and say in the text when you truncated

## Portability note, dated August 2026

The protocol is the same across providers and the envelope differs. Anthropic
sends a list of tool definitions with `name`, `description`, and
`input_schema`, and returns `tool_use` content blocks that you answer with
`tool_result` blocks carrying the matching `tool_use_id`. OpenAI wraps the
same information in a `function` object with a `parameters` field and returns
tool calls in their own array, answered with messages of role `tool`.

Write your schemas in a plain dictionary in one module, and convert to the
provider shape at the boundary. That is three lines today and it is what
keeps the model swappable, which is the same argument as week 1. Check the
current documentation before each edition: this is a product feature and it
moves faster than any textbook.

## Two habits that pay in week 10

Version the tool set alongside the prompt version, and record both next to
every score. Adding a tool changes the behaviour of every other tool, because
the model now has to choose between them, so a tool set change needs a
regression run rather than a code review.

Log the tool sequence on every request. A route decision was enough in week
3 because there was one decision. An agent produces a sequence, and the
sequence is the thing an evaluation harness joins against.
