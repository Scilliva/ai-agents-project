"""Stage: the vision step. Replaced in week 9.

Runs only when a request comes with an image (`python -m app.run --image
PATH "<request>"`). Until you wire yours in, it refuses: every read comes
back with `failure` set, so no field reaches the checks.

To replace it, copy your `labs/week09/starter/vision.py` and `perturb.py`
into `app/`, then change the sibling import in `vision.py`:

    from perturb import apply_variant
    from .perturb import apply_variant

Keep these names and signatures, because `pipeline.py` calls them:

    MODEL: str
    VisionResult                      fields, failure, ok, elapsed_s,
                                      prompt_tokens, output_tokens
    read_group(image_path, group, fields, variant="clean", replay=None,
               record=None, system=None, prompt=None) -> VisionResult
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .stub import stub

MODEL = "qwen3-vl:4b"


@dataclass
class VisionResult:
    doc: str
    group: str
    variant: str
    fields: dict[str, str | None] = field(default_factory=dict)
    failure: str | None = None
    elapsed_s: float = 0.0
    prompt_tokens: int = 0
    output_tokens: int = 0
    done_reason: str = ""
    raw_content: str = ""

    @property
    def ok(self) -> bool:
        return self.failure is None


@stub(week=9, does="refuses: reads nothing from the image")
def read_group(image_path: Path, group: str, fields: list[str],
               variant: str = "clean", replay=None, record=None,
               system: str | None = None,
               prompt: str | None = None) -> VisionResult:
    return VisionResult(doc=Path(image_path).stem, group=group,
                        variant=variant,
                        failure="stub: the week 9 vision step is not wired in")
