# Decision aid: does this need more than one agent

BPINFOR-132, week 5. One page. Keep it open while you argue about your project
architecture, and bring it to the week 14 showcase, where you will be asked to
justify what you built.

Sources: MAS-Dibia chapters 1, 2, and 11; ADP-Gulli chapters 6 and 7; the
"Planning" and "Agent Failure Modes and Evaluation" sections of AIE-Huyen
chapter 6.

## The five questions, in order

Ask them in this order and stop at the first one that gives you an answer. Each
rung down costs complexity, development time, and failure points, and buys
capability you may not need.

**1. Does the task require any action beyond producing text?**
No, then a direct model call is the answer. No loop, no tools, no agent. On
simple reasoning tasks a direct call scored 9.7 out of 10 in the MAS-Dibia
chapter 10 evaluation against 9.3 for an autonomous multi-agent system, at one
forty third of the tokens.

**2. Is the sequence of steps already known?**
Yes, then write a workflow. Your control flow, in your source code, readable in
a diff, with a cost you can compute before you run it. This is where weeks 3 and
4 live and it is where most production systems should stay.

**3. Does the task need one kind of expertise or several?**
One, then a single agent with the right tools. Do not split what does not
divide. Splitting by workflow step rather than by expertise gives you a chain
wearing a costume.

**4. Are the handoffs between the specialists well understood?**
Yes, then a multi-agent workflow with explicit control: sequential, conditional,
supervisor, or parallel. You keep bounded cost, per-node evaluation, and a
readable trace.

**5. Must the decomposition be discovered at runtime?**
Only here do you pay for an autonomous pattern: plan-based orchestration,
handoff, or a conversation-driven group. You are buying adaptability with
predictability, and the bill is decided by a model rather than by you.

## Signals that a second agent will help

- Two genuinely different kinds of expertise, with different tools and different
  failure profiles
- One agent must not see what the other sees, for context hygiene or for access
  control
- The critic role needs a fresh context, because self-critique inside one
  context inherits the first answer's mistakes
- The subtasks are independent enough to run in parallel and cut wall clock time
- You want to develop, evaluate, and version the parts separately
- The task is tool-heavy, which is where coordination overhead actually paid for
  itself in the published evaluations

## Signals that one agent with more tools is better

- The split is by workflow step, so it is a chain and belongs in your code
- The delegate would need the whole parent context anyway, so you are paying to
  copy it on every handoff
- You have not measured the single agent, so you cannot name what the second
  one fixes
- Latency matters and each handoff is another full round trip
- Nobody can say what the second agent knows that the first must not
- The diagram looked thin and the architecture is the answer to that

## Price list

| Pattern | Control | What you trade |
| Direct model call | You, entirely | Cheapest and least capable. No actions. |
| Single agent, tools | Model picks the next action | Bounded by a step cap you set |
| Sequential workflow | You, in code | Predictable cost and easy debugging, no flexibility |
| Conditional or supervisor workflow | You, with a classifier | Explicit branching, plus a classification that can be wrong |
| Parallel workflow | You, in code | Throughput, for a fan-in you have to design |
| Plan-based orchestration | An orchestrator model | Dynamic planning, for overhead on every step and a single point of failure |
| Handoff | Each agent locally | No central bottleneck, and a real risk of cycling |
| Conversation-driven group | Emergent, turn by turn | Maximum transparency, unbounded context growth, unbounded cost |

## Before you add anything, in order

1. Have you measured the current system? Architecture applied to an unmeasured
   failure is unfalsifiable.
2. Can you name the specific failure the new component prevents?
3. Can you cap it: steps, tool calls, revisions, delegations, rounds?
4. Can you evaluate it separately from everything else?
5. Can you say what it costs per task, in tokens, seconds, and euros?

If any answer is no, you are not ready to add it.

## The failure modes to design against

From MAS-Dibia chapter 11, section 3, chosen for what you can fix in a student
project.

| Failure mode | The fix |
| Instructions too thin | Expand them from observed failures. Good agent instructions read like job descriptions and are pages long. |
| Unclear termination | Write the success condition before the instructions, and make the agent state it when it stops. |
| The wrong pattern | Prototype the workflow, measure it, and convert only the section that fails. |
| Missing memory | Recognise re-derived context and store it. This is week 6. |
| No metacognition | Evaluate progress and replan, rather than retrying blindly. |
| No evaluation infrastructure | Build it. You cannot optimise what you cannot measure, and this is weeks 10 to 12. |

## Sentences worth being able to write in the project report

- "We prototyped a supervisor with three specialists, measured it against one
  agent with five tools on the same task set, and shipped the single agent
  because it was cheaper and no less accurate."
- "The plan is validated by five deterministic checks before execution. In
  our runs, N percent of plans were rejected, and the commonest reason was X."
- "We capped revisions at one. A second review round cost Y and changed no
  outcome in Z runs."
- "Adding the reviewer raised cost per task by N percent and caught one class
  of defect the test suite does not cover. Here is the defect."

Every one of these is stronger than a diagram.
