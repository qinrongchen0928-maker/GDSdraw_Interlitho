from __future__ import annotations


def positive_float(value: float, name: str) -> float:
    value = float(value)
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0.")
    return value


def fraction(value: float, name: str) -> float:
    value = float(value)
    if value <= 0 or value >= 1:
        raise ValueError(f"{name} must be between 0 and 1.")
    return value


def positive_int(value: int, name: str) -> int:
    value = int(value)
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0.")
    return value
