from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Iterable

import numpy as np
from PIL import Image

from .gds_backend import add_many, require_gdstk, write_library
from .geometry import lower_left_rectangle
from .validation import positive_float


@dataclass(frozen=True)
class ImageGenerationResult:
    data: bytes
    filename: str
    summary: dict[str, float | int | str | bool]


def image_bytes_to_mask(image_bytes: bytes, threshold: int = 128, invert: bool = False) -> np.ndarray:
    threshold = int(threshold)
    if threshold < 0 or threshold > 255:
        raise ValueError("Threshold must be between 0 and 255.")

    image = Image.open(BytesIO(image_bytes)).convert("L")
    gray = np.asarray(image)

    # Default rule: black pixels become structure. Inversion swaps that rule.
    return gray >= threshold if invert else gray < threshold


def horizontal_runs(mask: np.ndarray) -> Iterable[tuple[int, int, int]]:
    height, width = mask.shape
    for y in range(height):
        row = mask[y]
        x = 0
        while x < width:
            if not row[x]:
                x += 1
                continue
            start = x
            while x < width and row[x]:
                x += 1
            yield y, start, x


def merged_rectangles(mask: np.ndarray) -> list[tuple[int, int, int, int]]:
    active: dict[tuple[int, int], int] = {}
    rectangles: list[tuple[int, int, int, int]] = []
    height, _ = mask.shape

    for y in range(height):
        row_runs = {(start, end) for row, start, end in horizontal_runs(mask[y : y + 1])}
        next_active: dict[tuple[int, int], int] = {}

        for run in row_runs:
            next_active[run] = active.pop(run, y)

        for (start, end), y0 in active.items():
            rectangles.append((start, y0, end, y))

        active = next_active

    for (start, end), y0 in active.items():
        rectangles.append((start, y0, end, height))

    return rectangles


def generate_from_image(
    image_bytes: bytes,
    actual_length_um: float,
    actual_width_um: float,
    threshold: int = 128,
    invert: bool = False,
    layer: int = 0,
    max_pixels: int = 2_000_000,
    filename: str = "gdsdraw_image.gds",
) -> ImageGenerationResult:
    actual_length_um = positive_float(actual_length_um, "Actual length")
    actual_width_um = positive_float(actual_width_um, "Actual width")
    layer = int(layer)

    mask = image_bytes_to_mask(image_bytes, threshold=threshold, invert=invert)
    height_px, width_px = mask.shape
    pixel_count = width_px * height_px
    if pixel_count > max_pixels:
        raise ValueError(
            f"Image has {pixel_count:,} pixels, above the current limit of {max_pixels:,}. "
            "Resize it or increase the limit for local runs."
        )

    rectangles_px = merged_rectangles(mask)
    pixel_w = actual_length_um / width_px
    pixel_h = actual_width_um / height_px

    gdstk = require_gdstk()
    lib = gdstk.Library(name="GDSDRAW", unit=1e-6, precision=1e-9)
    main = lib.new_cell("MAIN")

    polygons = []
    for x0_px, y0_px, x1_px, y1_px in rectangles_px:
        x0 = x0_px * pixel_w
        x1 = x1_px * pixel_w
        # Image rows start at the top. GDS coordinates start at the bottom.
        y0 = actual_width_um - y1_px * pixel_h
        y1 = actual_width_um - y0_px * pixel_h
        polygons.append(lower_left_rectangle(x0, y0, x1, y1, layer=layer))

    add_many(main, polygons)

    return ImageGenerationResult(
        data=write_library(lib),
        filename=filename,
        summary={
            "mode": "image",
            "width_px": width_px,
            "height_px": height_px,
            "pixel_width_um": pixel_w,
            "pixel_height_um": pixel_h,
            "structure_pixels": int(mask.sum()),
            "rectangles_after_merge": len(rectangles_px),
            "inverted": invert,
            "threshold": int(threshold),
        },
    )
