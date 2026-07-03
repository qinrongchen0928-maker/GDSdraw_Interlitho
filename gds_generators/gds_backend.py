from __future__ import annotations

import os
import tempfile
from typing import Iterable


def require_gdstk():
    try:
        import gdstk  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "gdstk is required to write GDS files. Install dependencies with "
            "`python -m pip install -r requirements.txt`."
        ) from exc
    return gdstk


def write_library(library) -> bytes:
    fd, path = tempfile.mkstemp(suffix=".gds")
    os.close(fd)
    try:
        library.write_gds(path)
        with open(path, "rb") as handle:
            return handle.read()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def add_many(cell, polygons: Iterable) -> None:
    for polygon in polygons:
        cell.add(polygon)
