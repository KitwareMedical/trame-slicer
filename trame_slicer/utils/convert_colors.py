from __future__ import annotations


def rgb_float_to_hex(rgb_float: list[float]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(int(c * 255) for c in rgb_float))


def hex_to_rgb_float(color_hex: str):
    return [int(color_hex[i + 1 : i + 3], 16) / 255.0 for i in range(0, 6, 2)]
