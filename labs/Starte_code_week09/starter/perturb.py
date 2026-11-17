"""Degradations, and the vocabulary the whole session uses to name a run.

A variant is a string like `clean`, `scale=0.4`, or `blur=2.0`. It names one
image transformation, it is what the fixture is keyed on, and it is what goes
into DECISIONS.md beside the number it produced. One string, one condition,
so a result can never lose the conditions that produced it.

Downscaling alone turns out not to break this model, which is worth knowing
before you build a brittleness experiment on it. `WEEK09_FINDINGS.md` has the
table. Real documents arrive compressed, blurred, and skewed, so those are
here too.
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageFilter

# The sweep the lab ships a fixture for. Ordered from gentlest to harshest,
# which is the order a curve wants to be read in.
SWEEP = ["clean", "scale=0.6", "scale=0.4",
         "scale=0.4+jpeg=20", "scale=0.4+blur=1.0", "scale=0.4+rotate=4"]


def apply_variant(source: str | Path, variant: str) -> Image.Image:
    """Return the transformed image. `clean` returns the original.

    Steps compose with `+`, applied left to right, so
    `scale=0.4+jpeg=20` is a small image AND a compressed one. That is
    deliberate: it is what a photograph taken on a phone actually looks
    like, and it is also the only way the harsh end of the sweep runs fast
    enough to sit through. A full size blurred page makes this model think
    for minutes, which is a finding in itself and a bad lab exercise.
    """
    img = Image.open(source).convert("RGB")
    for step in variant.split("+"):
        img = _one(img, step.strip())
    return img


def _one(img: Image.Image, variant: str) -> Image.Image:
    if variant == "clean":
        return img
    name, _, arg = variant.partition("=")

    if name == "scale":
        factor = float(arg)
        return img.resize((max(1, int(img.width * factor)),
                           max(1, int(img.height * factor))))

    if name == "jpeg":
        # TODO 4a. Re-encode the image as JPEG at quality int(arg), then
        # reopen it, so the returned image carries the compression
        # artefacts. Save into an io.BytesIO rather than to disk.
        #
        # Why JPEG and not just a resize: artefacts cluster on sharp edges,
        # which is exactly where small dark text lives. A resize alone
        # keeps synthetic text crisp, which is measured in
        # WEEK09_FINDINGS.md and is why the sweep composes steps.
        raise NotImplementedError("TODO 4a: jpeg")

    if name == "occlude":
        left, top, right, bottom = (float(v) for v in arg.split(","))
        out = img.copy()
        box = (int(left * img.width), int(top * img.height),
               int(right * img.width), int(bottom * img.height))
        for x in range(box[0], box[2]):
            for y in range(box[1], box[3]):
                out.putpixel((x, y), (20, 20, 20))
        return out

    if name == "blur":
        # TODO 4b. One line, using ImageFilter.GaussianBlur and float(arg).
        raise NotImplementedError("TODO 4b: blur")

    if name == "rotate":
        # A page fed slightly crooked into a scanner. Expand so nothing is
        # cropped, and fill with white so the model sees paper.
        return img.rotate(float(arg), expand=True, fillcolor=(255, 255, 255),
                          resample=Image.BICUBIC)

    raise ValueError(f"unknown variant {variant!r}. Known: scale, jpeg, "
                     f"blur, rotate, occlude")


def describe(variant: str) -> str:
    """One line of run conditions, for the report."""
    return {
        "clean": "the original render, no degradation",
        "scale=0.6": "60 percent linear scale",
        "scale=0.4": "40 percent linear scale",
        "scale=0.4+jpeg=20": "40 percent scale, then JPEG quality 20",
        "scale=0.4+blur=1.0": "40 percent scale, then a 1 pixel blur",
        "scale=0.4+rotate=4": "40 percent scale, then rotated 4 degrees",
    }.get(variant, variant)
