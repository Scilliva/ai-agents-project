"""Block 4. Change one thing nobody would flag in review, and measure it.

    python 03_sensitivity.py --variant role --replay
    python 03_sensitivity.py --variant english_only

Fifteen minutes, one variant per group, so that the plenary has four results
instead of one. Your instructor will assign you one.

The point of this block is not which variant wins. It is that a change no
reviewer would comment on moves a measured number, which is why a prompt is
a versioned artifact and why "I improved the prompt" is not a claim anybody
should accept without a table.

One TODO marker.
"""

from __future__ import annotations

import argparse

from documents import DOCS, GOLD
from extractor import SYSTEM_ZERO_SHOT, get_client, run_variant
from scoring import compare

from project.trace import write_json

VARIANTS = ("baseline", "role", "reordered", "no_delimiter", "english_only")


# --------------------------------------------------------------------------
# TODO 8. Build one variant and measure it against your few-shot baseline.
# --------------------------------------------------------------------------

def build_system(variant: str) -> str:
    """Return the system prompt for one variant.

    Start from your few-shot prompt from block 3, and change exactly one
    thing. Not two. The whole value of this block is that only one thing
    moved.

    baseline       your few-shot prompt from block 3, unchanged
    role           prepend "You are a senior service desk analyst." and
                   nothing else. On a task with closed label sets and a
                   schema, a persona usually buys close to nothing and costs
                   tokens on every call. If you find otherwise, that is a
                   genuinely interesting result worth reporting.
    reordered      the same examples in a different order. Nothing about the
                   task changed. Predict the effect before you run it, then
                   write down whether you were right.
    no_delimiter   remove whatever separates the document from the
                   instruction. Watch what happens on the longer messages.
                   This one is a preview of week 12: if the model cannot
                   tell your instruction from the data, neither can your
                   defenses.
    english_only   replace your non-English examples with English ones,
                   keeping the same count. Then read the score per language
                   as well as overall. Be careful here: the story you expect
                   is that non-English documents suffer, and the corpus has
                   five, three, and two documents per language, which is not
                   enough to support that claim even if the numbers point
                   that way. Report what moved, and say what sample would be
                   needed to attribute it. Week 13 asks who a system works
                   for, and this is what it costs to answer with evidence.
    """
    raise NotImplementedError("TODO 8: build the variant")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=VARIANTS, required=True)
    ap.add_argument("--replay", action="store_true")
    args = ap.parse_args()

    client = get_client(args.replay)

    base = run_variant(client, build_system("baseline"), "baseline",
                       DOCS, GOLD)[0]
    if args.variant == "baseline":
        return 0
    other = run_variant(client, build_system(args.variant), args.variant,
                        DOCS, GOLD)[0]

    print(compare(base, other, "baseline", args.variant))

    # Per language, which is where the english_only variant shows its hand
    # and where an overall average would have hidden it entirely.
    for lang in ("en", "fr", "de"):
        ids = {d.id for d in DOCS if d.lang == lang}
        n = len(ids)
        print(f"  {lang}: {n} documents"
              f"   baseline field errors "
              f"{sum(1 for f in base.failures if f[0] in ids)}"
              f"   {args.variant} field errors "
              f"{sum(1 for f in other.failures if f[0] in ids)}")

    write_json(f"artifacts/week02_sensitivity_{args.variant}.json", {
        "variant": args.variant,
        "baseline_hits": base.hits, "variant_hits": other.hits,
    })

    # Write in DECISIONS.md: what you changed, what moved, and by how much.
    # If nothing moved, say so. A variant that changes nothing measurable is
    # a real result and it is worth reporting, because it tells the room
    # which knobs are worth arguing about and which are superstition.

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
