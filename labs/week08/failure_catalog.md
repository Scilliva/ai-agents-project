# The failure catalog

One page on the injection harness in `starter/faults.py`. Every fault kind,
what it simulates, which of the four layers from the lecture it belongs to,
the response that ought to handle it, and the mistake groups usually make.

Keep this open during block 1. Checked August 2026.

## How to aim a fault

```
target : kind [ @rate ]
```

- `target` is a tool name, one of `search`, `keyword_fallback`, or `fees`
- `kind` is one of the eight below
- `rate` is the probability, between 0 and 1, default 1.0

Rules are comma separated and parsed by `FaultPlan.parse`, which rejects any
kind that is not in `FAULTS` rather than ignoring it quietly:

```python
from faults import FaultPlan

plan = FaultPlan.parse("search:timeout@0.6", seed=7)
plan = FaultPlan.parse("fees:drift,search:slow@0.1")
```

There is no wildcard target and no delayed start. Both are easy to add and
neither is needed for the sweep this session runs, so the parser stays small
enough to read in one sitting. If you want a fault that only fires from the
third call onward, that is a rate of 1.0 plus two lines in `_fires`, and it
is a reasonable thing to write for your own project.

Determinism: `_fires` hashes the seed, the tool name, and the call index with
SHA-256 and compares the result to the rate. It never touches the global
`random` module, so injecting faults cannot perturb any other sampling in
your program, and it holds no state beyond a per-tool call counter. Same
seed, same failures, every time, on every machine.

## The eight kinds

These are the keys of `FAULTS` in `faults.py`. The names in this table and
the names in that dict are the same strings, so `--faults` accepts exactly
this list and rejects anything else.

| Kind | Simulates | Layer | Correct response | The usual mistake |
| `timeout` | The service did not answer within the client deadline | Transport | Retry with exponential backoff and jitter, then fall back | A fixed sleep, or no cap, so a broken dependency becomes an infinite loop |
| `rate_limit` | HTTP 429, you are sending faster than your quota | Transport | Retry with backoff. Against a real upstream, prefer its `Retry-After` header to your own guess. | Retrying immediately, which is how a rate limit becomes an outage |
| `server_error` | HTTP 500 from somebody else's service | Transport | Retry a bounded number of times, then fall back or degrade | Treating every 5xx as fatal, or retrying a 500 forever |
| `malformed` | A 200 whose body is not the contract at all, here an HTML error page | Contract | Validate at the boundary, then repair, fall back, or degrade | Retrying, which returns the same broken payload and a larger bill |
| `empty` | A well formed response with no content in it | Contract | Detect the empty case explicitly and degrade, saying so | Treating an empty list as a successful search and answering anyway |
| `slow` | The call succeeds, eventually, well past the deadline | Transport | A deadline on the step, and a decision about what to do when it passes | No deadline at all, so one slow service holds the whole run open |
| `drift` | A valid response with a renamed key, `fee_eur` becomes `amount_eur` | Contract | Validation catches it. Then either map the new shape or degrade. | Retrying. Nothing about the call failed, so nothing about retrying helps. |
| `flaky` | Fails once, then succeeds. The control case. | Transport | A single retry makes it disappear entirely | Concluding from this one case that retry is what robustness means |

A ninth kind, `auth_error` for an HTTP 401, is deliberately not shipped. It
is the exercise at the end of this file, because it is the cleanest case of
a transport failure that must never be retried, and writing it yourself is
worth more than reading it here.

The four layers are from the lecture: transport, contract, judgment, and
goal. The harness can only reach the first two, and that limit is worth
stating out loud. Judgment failures and goal failures cannot be injected from
outside, because nothing about them is an error. They are what evaluation in
week 10 and guardrails in week 11 are for.

## The one to stare at

`drift` returns semantics-preserving change: the key `fee_eur` comes back as
`amount_eur` and the number under it is untouched. Nothing is wrong. A human
reading the payload would say it is fine. Your code, which asked for
`fee_eur`, will disagree, and no retry policy will ever help.

Watch the attempt count on this row, because it is the number that tells you
whether you built a ladder or a retry wrapper. It should be one. If the fees
step reports three attempts under `drift`, then `is_retryable` has put a
contract failure on the retryable side and the policy is paying three times
for the same wrong answer.

This is what AAR-Rabanser calls environment robustness, and the paper reports
that current models handle it, and infrastructure faults, fairly well, while
remaining brittle to paraphrasing of the task itself. The uncomfortable
implication for today: the retries you build this afternoon are necessary and
they are not sufficient, and the more dangerous fragility is on the input
side, where nobody thinks to test.

## Reading the record

Every injected fault is appended to `FaultPlan.fired`, as `tool:kind#index`,
and every recovery attempt comes back inside a `StepResult`. Together they
answer four questions that no log line can answer on its own:

- what was injected, on which call, on which attempt
- how many attempts the policy made, and how long it waited between them
- whether the fallback fired, which is otherwise invisible
- what the user was finally told, and whether it was honest about the gap

`01_survive.py` prints the matrix and writes the full detail to
`artifacts/week08_faults_baseline.json` and
`artifacts/week08_faults_hardened.json`, one file per configuration so the
two can be compared without rerunning either. Those files are what week 10
reloads.

## Fault matrices worth running

`01_survive.py` runs the standard sweep on its own: eight kinds, aimed one at
a time, with the two configurations that make the comparison.

```bash
python 01_survive.py --baseline
```

```bash
python 01_survive.py
```

Run the baseline first and keep both tables. The point of the session is the
difference between them, and the column to compare is `WRONG` rather than
`correct`.

Past that, the interesting matrices are the ones you aim yourself. The tools
are named `search`, `keyword_fallback`, and `fees`, and a plan is built in
Python rather than on the command line:

```python
from faults import FaultPlan

# correlated failure: one broken upstream takes out both live steps at once
plan = FaultPlan.parse("search:server_error@0.4,fees:server_error@0.4", seed=11)

# intermittent, which is harder to handle than total failure and more realistic
plan = FaultPlan.parse("search:timeout@0.35", seed=3)

# the fallback is a dependency too, and it is the one nobody tests
plan = FaultPlan.parse("search:timeout@1.0,keyword_fallback:timeout@1.0")
```

Note what the syntax does and does not give you. A rule is `tool:kind@rate`,
the rate is a probability rather than a schedule, and there is no wildcard,
so a correlated failure is written as one rule per tool. Whether a given call
fires is decided by hashing the seed, the tool name, and the call index, so
the same seed reproduces the same run exactly, and changing the seed gives
you a different draw rather than a different rate.

The second one is the interesting stretch. Per-step recovery quietly assumes
that steps fail independently. They do not, when the cause is one shared
service, and a system that retries four steps against the same dead
dependency simply takes four times as long to fail.

## Adding your own fault kind

Add the name and its one-line description to `FAULTS`, then one branch in
`FaultPlan.apply`. Keep it deterministic. `apply` counts the calls it has
seen per tool and asks `_fires`, which hashes the seed, the tool name, and
the call index with SHA-256 and compares that to the rate. Never reach for
the global `random` module: the whole fault matrix has to reproduce from a
seed, or the numbers in your report mean nothing.

Start with `auth_error`, an HTTP 401, because it is the one the retry ladder
gets wrong by default. Raise a new `AuthError` exception, and then leave
`RETRYABLE` alone so that `is_retryable` returns False for it. Run the
matrix and check the attempt count on that row is one. If it is three, your
policy is retrying a broken credential, which on a real upstream is how you
get the account locked rather than the token refreshed.

Note what `auth_error` and `drift` have in common and where they differ.
Neither is retryable, so they sit on the same side of `is_retryable`, but
for opposite reasons: the 401 is a transport failure that will never
succeed, and the drift is a transport success whose payload broke the
contract. Two different layers, one policy decision. That is the argument
for classifying by "will a retry help" rather than by HTTP status.

Two more worth writing when your project is further along: a truncated
response, which is the most common real failure with a model output cap, and
a duplicate response, which is what a retried non-idempotent write produces
and which your own code should be the thing that prevents.
