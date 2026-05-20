from __future__ import annotations


def as_rgba_hex(hex_channels: str) -> str:
    """
    Pads input hex string to RGBA (8 characters) by adding FF values.
    """
    hex_val = hex_channels.lstrip("#")
    return f"#{hex_val.ljust(8, 'f')[:8]}"


def float_channels_to_hex(float_channels: list[float]) -> str:
    """
    Converts a list of input color channels to hex format.
    Supports arbitrary length of color components (e.g., RGB, RG, RGBA).
    """
    return "#" + "".join([f"{int(c * 255):02x}" for c in float_channels])


def hex_to_float_channels(hex_channels: str) -> list[float]:
    """
    Converts a list of input hex colors channels prefixed by # to the equivalent float color channels.
    Supports arbitrary length of color hex channels (e.g., RGB, RG, RGBA).
    """
    return [int(hex_channels[i + 1 : i + 3], 16) / 255.0 for i in range(0, len(hex_channels) - 1, 2)]


def rgb_float_to_hex(rgb_float: list[float]) -> str:
    assert len(rgb_float) == 3
    return float_channels_to_hex(rgb_float)


def hex_to_rgb_float(color_hex: str) -> list[float]:
    assert len(color_hex) == 7
    return hex_to_float_channels(color_hex)
