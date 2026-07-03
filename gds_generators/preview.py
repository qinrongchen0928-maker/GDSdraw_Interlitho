from __future__ import annotations

from io import BytesIO
from math import floor

import numpy as np
from PIL import Image, ImageDraw


BG = (248, 249, 250)
INK = (20, 24, 31)
GRID = (210, 216, 224)
EDGE = (96, 111, 128)


def _canvas_size(width_um: float, height_um: float, max_side: int = 900) -> tuple[int, int, float]:
    if width_um <= 0 or height_um <= 0:
        raise ValueError("Preview dimensions must be greater than 0.")
    scale = max_side / max(width_um, height_um)
    width_px = max(240, int(round(width_um * scale)))
    height_px = max(160, int(round(height_um * scale)))
    scale = min(width_px / width_um, height_px / height_um)
    return width_px, height_px, scale


def _to_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _draw_frame(draw: ImageDraw.ImageDraw, width_px: int, height_px: int) -> None:
    draw.rectangle((0, 0, width_px - 1, height_px - 1), outline=EDGE, width=2)


def _draw_1d_grating(draw: ImageDraw.ImageDraw, period: float, duty: float, total_l: float, total_w: float, scale: float, invert: bool = False) -> None:
    columns = floor(total_l / period)
    line_w = period * duty
    if invert:
        draw.rectangle((0, 0, columns * period * scale, total_w * scale), fill=INK)
    for col in range(columns):
        x0 = col * period * scale
        x1 = (col * period + line_w) * scale
        draw.rectangle((x0, 0, x1, total_w * scale), fill=BG if invert else INK)


def _draw_2d_shape(
    draw: ImageDraw.ImageDraw,
    shape: str,
    period_x: float,
    period_y: float,
    total_l: float,
    total_w: float,
    scale: float,
    diameter: float | None = None,
    square_side: float | None = None,
    rect_l: float | None = None,
    rect_w: float | None = None,
    invert: bool = False,
) -> None:
    cols = floor(total_l / period_x)
    rows = floor(total_w / period_y)
    max_items = 25_000
    step = max(1, int((cols * rows / max_items) ** 0.5))

    for row in range(0, rows, step):
        cy = (row + 0.5) * period_y * scale
        for col in range(0, cols, step):
            cx = (col + 0.5) * period_x * scale
            if invert:
                x0 = col * period_x * scale
                y0 = row * period_y * scale
                x1 = (col + step) * period_x * scale
                y1 = (row + step) * period_y * scale
                draw.rectangle((x0, y0, x1, y1), fill=INK)
            fill = BG if invert else INK
            if shape == "circle":
                d = float(diameter or 0) * scale
                draw.ellipse((cx - d / 2, cy - d / 2, cx + d / 2, cy + d / 2), fill=fill)
            elif shape == "square":
                s = float(square_side or 0) * scale
                draw.rectangle((cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2), fill=fill)
            else:
                w = float(rect_l or 0) * scale
                h = float(rect_w or 0) * scale
                draw.rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), fill=fill)


def periodic_overview_1d(period: float, duty: float, total_l: float, total_w: float, invert: bool = False) -> bytes:
    width_px, height_px, scale = _canvas_size(total_l, total_w)
    image = Image.new("RGB", (width_px, height_px), BG)
    draw = ImageDraw.Draw(image)
    _draw_1d_grating(draw, period, duty, total_l, total_w, scale, invert=invert)
    _draw_frame(draw, width_px, height_px)
    return _to_bytes(image)


def periodic_detail_1d(period: float, duty: float, total_w: float, invert: bool = False) -> bytes:
    width_um = 3 * period
    height_um = min(total_w, max(period * 2, period / max(duty, 0.01)))
    width_px, height_px, scale = _canvas_size(width_um, height_um, max_side=760)
    image = Image.new("RGB", (width_px, height_px), BG)
    draw = ImageDraw.Draw(image)
    for col in range(4):
        x = col * period * scale
        draw.line((x, 0, x, height_px), fill=GRID, width=1)
    _draw_1d_grating(draw, period, duty, width_um, height_um, scale, invert=invert)
    _draw_frame(draw, width_px, height_px)
    return _to_bytes(image)


def periodic_overview_2d(
    shape: str,
    period_x: float,
    period_y: float,
    total_l: float,
    total_w: float,
    diameter: float | None = None,
    square_side: float | None = None,
    rect_l: float | None = None,
    rect_w: float | None = None,
    invert: bool = False,
) -> bytes:
    width_px, height_px, scale = _canvas_size(total_l, total_w)
    image = Image.new("RGB", (width_px, height_px), BG)
    draw = ImageDraw.Draw(image)
    _draw_2d_shape(draw, shape, period_x, period_y, total_l, total_w, scale, diameter, square_side, rect_l, rect_w, invert=invert)
    _draw_frame(draw, width_px, height_px)
    return _to_bytes(image)


def periodic_detail_2d(
    shape: str,
    period_x: float,
    period_y: float,
    diameter: float | None = None,
    square_side: float | None = None,
    rect_l: float | None = None,
    rect_w: float | None = None,
    invert: bool = False,
) -> bytes:
    width_um = 3 * period_x
    height_um = 3 * period_y
    width_px, height_px, scale = _canvas_size(width_um, height_um, max_side=760)
    image = Image.new("RGB", (width_px, height_px), BG)
    draw = ImageDraw.Draw(image)
    for i in range(4):
        draw.line((i * period_x * scale, 0, i * period_x * scale, height_px), fill=GRID, width=1)
        draw.line((0, i * period_y * scale, width_px, i * period_y * scale), fill=GRID, width=1)
    _draw_2d_shape(draw, shape, period_x, period_y, width_um, height_um, scale, diameter, square_side, rect_l, rect_w, invert=invert)
    _draw_frame(draw, width_px, height_px)
    return _to_bytes(image)


def mask_overview(mask: np.ndarray, max_side: int = 900) -> bytes:
    image = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L")
    image.thumbnail((max_side, max_side), Image.Resampling.NEAREST)
    rgb = Image.new("RGB", image.size, BG)
    rgb.paste(Image.merge("RGB", (image, image, image)))
    draw = ImageDraw.Draw(rgb)
    _draw_frame(draw, rgb.width, rgb.height)
    return _to_bytes(rgb)
