"""Block 2. The zero-shot baseline, scored per field.

    python 01_zero_shot.py --replay     # the shipped recording, instant
    python 01_zero_shot.py              # your own model, about 45 seconds

Develop your scorer against `--replay`. The recording holds every model
answer for both variants, so your scorer runs in well under a second and you
can iterate on it properly instead of waiting forty-five seconds to find out
you compared the wrong field.

The recording contains real failures, because the model really does make
them. If your scorer reports forty out of forty, your scorer does nothing.

One TODO marker here. TODO 1 to 4 live in extractor.py and scoring.py, and
this file will not run until they are done.
"""

from __future__ import annotations

import argparse

from documents import DOCS, GOLD
from extractor import (PROMPT_VERSION, SYSTEM_ZERO_SHOT, get_client,
                       run_variant)

from project.trace import write_json


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    args = ap.parse_args()

    client = get_client(args.replay)
    board, records, metas = run_variant(client, SYSTEM_ZERO_SHOT,
                                        "zero-shot", DOCS, GOLD)

    if board.failures:
        print("failures worth reading:")
        for doc_id, fieldname, note in board.failures[:10]:
            print(f"  {doc_id}  {fieldname:<9} {note}")

    write_json("artifacts/week02_zero_shot.json", {
        "variant": "zero-shot",
        "prompt_version": PROMPT_VERSION,
        "hits": board.hits, "total": board.total, "invalid": board.invalid,
    })

    # TODO 7. Write the gold set into the project spine.
    #
    #   Build a GoldSet out of the ten documents and their annotations and
    #   write it to artifacts/goldset.json with
    #   project.trace.write_json(...).
    #
    #   For each document, one GoldCase with:
    #     case_id           the document id
    #     week_added        2
    #     question          the document text
    #     expected          the gold annotation, as a dict
    #     expected_behavior one sentence a colleague could grade against.
    #                       "extracts category access and urgency standard,
    #                       with no due date because the message only says
    #                       'before the end of the month'" is a good one.
    #                       "works" is not.
    #     slice_tags        at least the language, so week 10 can report per
    #                       language instead of as one average
    #
    #   This is not busywork and it is not for today. Week 3 adds route
    #   labels to this file, week 7 adds retrieval questions, and week 10
    #   builds the evaluation harness on whatever is in it by then. Ten
    #   careful cases now is the cheapest week 10 you will ever have.
    #
    #   Then run: python -m project.verify

    from dataclasses import asdict

    gold_cases = []
    gold_ids = list(GOLD.keys())

    for i, doc_id in enumerate(gold_ids):
        raw_doc = DOCS[i]
        if isinstance(raw_doc, str):
            doc_text = raw_doc
        else:
            doc_text = raw_doc.text

        gold_annotation = GOLD[doc_id]
        
        if isinstance(gold_annotation, dict):
            expected_dict = gold_annotation
            gold_id = gold_annotation.get("id", doc_id)
        else:
            expected_dict = asdict(gold_annotation)
            gold_id = getattr(gold_annotation, "id", doc_id)

        behavior = (
            "Extracts category, urgency, due_date, and quote verbatim from the text. "
            "due_date is None if no specific ISO date is mentioned. "
            "quote must be a substring of the source text."
        )
        
        lang_tag = "en"
        
        case = {
            "case_id": gold_id,
            "week_added": 2,
            "question": doc_text,
            "expected": expected_dict,
            "expected_behavior": behavior,
            "slice_tags": [lang_tag]
        }
        gold_cases.append(case)

    gold_set = {
        "name": "week02_zero_shot_gold",
        "description": "Gold standard annotations for the 10-document zero-shot baseline.",
        "cases": gold_cases
    }

    write_json("artifacts/goldset.json", gold_set)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
