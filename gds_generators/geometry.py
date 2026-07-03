from __future__ import annotations

import math

from .gds_backend import require_gdstk


def rectangle_polygon(width_um: float, height_um: float, layer: int = 0):
    gdstk = require_gdstk()
    return gdstk.rectangle(
        (-width_um / 2.0, -height_um / 2.0),
        (width_um / 2.0, height_um / 2.0),
        layer=layer,
    )


def lower_left_rectangle(x0: float, y0: float, x1: float, y1: float, layer: int = 0):
    gdstk = require_gdstk()
    return gdstk.rectangle((x0, y0), (x1, y1), layer=layer)


def circle_polygon(diameter_um: float, points: int = 96, layer: int = 0):
    gdstk = require_gdstk()
    radius = diameter_um / 2.0
    vertices = []
    for index in range(points):
        angle = 2.0 * math.pi * index / points
        vertices.append((radius * math.cos(angle), radius * math.sin(angle)))
    return gdstk.Polygon(vertices, layer=layer)


def diamond_polygon(side_um: float, layer: int = 0):
    gdstk = require_gdstk()
    d = side_um * math.sqrt(2) / 2.0
    return gdstk.Polygon([(d, 0), (0, d), (-d, 0), (0, -d)], layer=layer)
