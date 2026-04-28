from __future__ import annotations


def rgba_float_to_hex(rgb_float: list[float]) -> str:
    return "#" + "".join([f"{int(c * 255):02x}" for c in rgb_float])


def hex_to_rgba_float(color_hex: str):
    return [int(color_hex[i + 1 : i + 3], 16) / 255.0 for i in range(0, len(color_hex) - 1, 2)]
