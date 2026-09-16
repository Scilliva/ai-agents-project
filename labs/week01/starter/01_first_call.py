"""Block 2. One call, and everything you can learn from it.

    python 01_first_call.py

A call that prints only the answer is not finished. By the end of this file
you print four things and can explain all four, and you write the run into
`artifacts/traces.jsonl` in the shape every later week reads.

Three TODO markers. Do them in order.
"""

from __future__ import annotations

import time

from openai import OpenAI

from project.models import BASE_URL, API_KEY, SMALL
from project.prices import estimate
from project.trace import TraceRecorder, local_conditions

QUESTION = ("A resident asks how to register a change of address. "
            "Answer in two sentences.")


def main() -> int:
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    rec = TraceRecorder(
        week=1,
        case_id="W1-first-call",
        conditions=local_conditions(SMALL.name, temperature=0.0),
        user_input=QUESTION,
    )

    with rec.step("model", SMALL.name) as step:
        started = time.perf_counter()

        # TODO 1. Make the call.
        #   client.chat.completions.create(...) with:
        #     model=SMALL.name
        #     messages=[{"role": "user", "content": QUESTION}]
        #     temperature=0.0
        #     max_tokens=200
        #   Assign the result to `reply`.
        reply = None

        elapsed = time.perf_counter() - started

        if reply is None:
            print("TODO 1 is not done yet: `reply` is still None.")
            print("Open this file and make the call. The four lines you "
                  "need are in the comment above.")
            return 1

        step.tokens(reply.usage.prompt_tokens, reply.usage.completion_tokens)
        step.detail(finish_reason=reply.choices[0].finish_reason)

    # TODO 2. Print four things, and be ready to say what each one means.
    #
    #   a. the answer text            reply.choices[0].message.content
    #   b. the finish reason          reply.choices[0].finish_reason
    #      What would it say if the answer had been cut off, and how would
    #      your program know the difference between that and a short answer?
    #   c. the token counts           reply.usage.prompt_tokens
    #                                 reply.usage.completion_tokens
    #      Which of the two do you control, and how?
    #   d. the elapsed time           `elapsed`, computed above
    #      Which part of it would a user actually feel?
    #
    print("\n--- TODO 2: print the four things here ---\n")

    # TODO 3. Close the trace.
    #   Call rec.finish(...) with:
    #     output=  the answer text
    #     outcome= "ok"
    #   It writes to artifacts/traces.jsonl by itself.
    #
    #   Then run, from your repository root:
    #     python -m project.verify
    #   It should report one record in traces.jsonl. From week 4 onward
    #   every run your system makes lands in that file, and week 10 builds
    #   the evaluation harness on it.

    # A free number, so that cost is visible from day one. Local calls cost
    # nothing, which is convenient and also a distortion, so the course keeps
    # an estimate of what the same call would cost on a metered endpoint.
    if reply is not None:
        est = estimate(reply.usage.prompt_tokens,
                       reply.usage.completion_tokens, tier="small")
        print(est.summary())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
