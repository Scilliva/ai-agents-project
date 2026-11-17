"""RAGAS faithfulness over the week 7 retrieval artifact. The stretch path.

Not part of the ninety minutes. The session already has three blocks, and
this is here because RAG-specific metrics are the one thing DeepEval's
general judge does not give you: faithfulness scores an answer against the
passages that were actually retrieved, rather than against a reference
answer, which is the question a RAG pipeline actually raises.

Checked against RAGAS 0.4.3 in August 2026. This API moved twice in a year,
so re-check it before you trust it:

  * the metrics live in `ragas.metrics.collections`, not `ragas.metrics`
  * `llm_factory` wants an OpenAI-shaped client, which is how it reaches a
    local endpoint with no API key that means anything
  * `ascore` takes keyword arguments and returns an object with `.value`
  * `langchain-community` must stay below 0.4 or the import fails

    python ragas_metrics.py
"""

from __future__ import annotations

import asyncio

MODEL = "qwen3:4b-instruct"
BASE_URL = "http://127.0.0.1:11434/v1"

CONTEXT = [
    "The residential parking vignette costs 60 EUR per year.",
    "Apply at the Bierger-Center with proof of residence.",
]
QUESTION = "How much is the vignette and where do I apply?"
ANSWERS = [
    ("grounded", "The vignette costs 60 EUR per year and you apply at the "
                 "Bierger-Center."),
    ("one invented fee", "The vignette costs 85 EUR per year and you apply "
                         "at the Bierger-Center."),
    ("wholly invented", "You must email the mayor and wait six weeks for a "
                        "decision."),
]


async def main() -> int:
    from openai import AsyncOpenAI
    from ragas.llms import llm_factory
    from ragas.metrics.collections import Faithfulness

    client = AsyncOpenAI(base_url=BASE_URL, api_key="ollama")
    metric = Faithfulness(llm=llm_factory(MODEL, provider="openai",
                                          client=client))

    print(f"{'answer':<20}{'faithfulness':>14}")
    print("-" * 34)
    for tag, answer in ANSWERS:
        result = await metric.ascore(user_input=QUESTION, response=answer,
                                     retrieved_contexts=CONTEXT)
        print(f"{tag:<20}{result.value:>14.2f}")

    print("\n  Faithfulness asks a different question from the week 10 judge.")
    print("  The judge compares an answer to a REFERENCE. Faithfulness")
    print("  compares it to the passages your retriever actually returned,")
    print("  so it separates 'the generator invented something' from 'the")
    print("  retriever fetched the wrong passage'. Week 7 measured the")
    print("  second half. This measures the first.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
