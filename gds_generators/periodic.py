from __future__ import annotations

import math
from dataclasses import dataclass

from .gds_backend import require_gdstk, write_library
from .geometry import circle_polygon, rectangle_polygon
from .validation import fraction, positive_float, positive_int


@dataclass(frozen=True)
class GenerationResult:
    data: bytes
    filename: str
    summary: dict[str, float | int | str | bool]


def _new_library():
    gdstk = require_gdstk()
    return gdstk.Library(name="GDSDRAW", unit=1e-6, precision=1e-9)


def _cell_array(unit_cell, columns: int, rows: int, spacing: tuple[float, float], origin: tuple[float, float]):
    gdstk = require_gdstk()
    return gdstk.Reference(unit_cell, origin=origin, columns=columns, rows=rows, spacing=spacing)


def _rect(x0: float, y0: float, x1: float, y1: float, layer: int):
    gdstk = require_gdstk()
    return gdstk.rectangle((x0, y0), (x1, y1), layer=layer)


def _unit_complement(base_polygon, cut_polygon, layer: int):
    gdstk = require_gdstk()
    return gdstk.boolean([base_polygon], [cut_polygon], "not", layer=layer)


def generate_1d_grating(
    period_um: float,
    duty_cycle: float,
    total_length_um: float,
    total_width_um: float,
    layer: int = 0,
    invert: bool = False,
    filename: str = "gdsdraw_1d_grating.gds",
) -> GenerationResult:
    period_um = positive_float(period_um, "Period")
    duty_cycle = fraction(duty_cycle, "Duty cycle")
    total_length_um = positive_float(total_length_um, "Total length")
    total_width_um = positive_float(total_width_um, "Total width")
    layer = int(layer)

    columns = positive_int(math.floor(total_length_um / period_um), "Number of grating periods")
    line_width = period_um * duty_cycle

    lib = _new_library()
    unit = lib.new_cell("UNIT_1D_INVERTED" if invert else "UNIT_1D_LINE")
    if invert:
        unit.add(_rect(line_width, 0, period_um, total_width_um, layer=layer))
    else:
        unit.add(_rect(0, 0, line_width, total_width_um, layer=layer))

    main = lib.new_cell("MAIN")
    main.add(_cell_array(unit, columns=columns, rows=1, spacing=(period_um, 0), origin=(0, 0)))

    return GenerationResult(
        data=write_library(lib),
        filename=filename,
        summary={
            "mode": "1D grating",
            "period_um": period_um,
            "duty_cycle": duty_cycle,
            "line_width_um": line_width,
            "inverted": invert,
            "columns": columns,
            "rows": 1,
            "array_references": 1,
        },
    )


def generate_2d_periodic(
    shape: str,
    period_x_um: float,
    period_y_um: float,
    total_length_um: float,
    total_width_um: float,
    diameter_um: float | None = None,
    square_side_um: float | None = None,
    rectangle_length_um: float | None = None,
    rectangle_width_um: float | None = None,
    circle_points: int = 96,
    layer: int = 0,
    invert: bool = False,
    filename: str = "gdsdraw_2d_periodic.gds",
) -> GenerationResult:
    shape = shape.lower().strip()
    period_x_um = positive_float(period_x_um, "X period")
    period_y_um = positive_float(period_y_um, "Y period")
    total_length_um = positive_float(total_length_um, "Total length")
    total_width_um = positive_float(total_width_um, "Total width")
    circle_points = positive_int(circle_points, "Circle points")
    layer = int(layer)

    columns = positive_int(math.floor(total_length_um / period_x_um), "Number of columns")
    rows = positive_int(math.floor(total_width_um / period_y_um), "Number of rows")

    lib = _new_library()
    unit = lib.new_cell(f"UNIT_{shape.upper()}_{'INVERTED' if invert else 'NORMAL'}")

    if shape == "circle":
        diameter = positive_float(diameter_um or 0, "Diameter")
        shape_polygon = circle_polygon(diameter, points=circle_points, layer=layer)
        size_summary = {"diameter_um": diameter}
    elif shape == "square":
        side = positive_float(square_side_um or 0, "Square side")
        shape_polygon = rectangle_polygon(side, side, layer=layer)
        size_summary = {"square_side_um": side}
    elif shape == "rectangle":
        length = positive_float(rectangle_length_um or 0, "Rectangle length")
        width = positive_float(rectangle_width_um or 0, "Rectangle width")
        shape_polygon = rectangle_polygon(length, width, layer=layer)
        size_summary = {"rectangle_length_um": length, "rectangle_width_um": width}
    else:
        raise ValueError("Shape must be circle, square, or rectangle.")

    if invert:
        base = _rect(-period_x_um / 2.0, -period_y_um / 2.0, period_x_um / 2.0, period_y_um / 2.0, layer=layer)
        complement = _unit_complement(base, shape_polygon, layer=layer)
        if not complement:
            raise ValueError("Inverted unit is empty. Make the structure smaller than the period.")
        unit.add(*complement)
    else:
        unit.add(shape_polygon)

    main = lib.new_cell("MAIN")
    main.add(_cell_array(unit, columns=columns, rows=rows, spacing=(period_x_um, period_y_um), origin=(period_x_um / 2.0, period_y_um / 2.0)))

    return GenerationResult(
        data=write_library(lib),
        filename=filename,
        summary={
            "mode": "2D periodic",
            "shape": shape,
            "period_x_um": period_x_um,
            "period_y_um": period_y_um,
            "columns": columns,
            "rows": rows,
            "inverted": invert,
            "array_references": 1,
            **size_summary,
        },
    )
