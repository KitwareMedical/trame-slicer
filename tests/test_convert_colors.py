import pytest

from trame_slicer.utils import (
    as_rgba_hex,
    float_channels_to_hex,
    hex_to_float_channels,
    hex_to_rgb_float,
    rgb_float_to_hex,
)


@pytest.mark.parametrize(
    ("hex_channels", "expected"),
    [
        ("#ffffff", "#ffffffff"),
        ("#000000", "#000000ff"),
        ("#abc123", "#abc123ff"),
        ("#fff", "#ffffffff"),
        ("#ffffffffffff", "#ffffffff"),
    ],
)
def test_as_rgba_hex(hex_channels, expected):
    assert as_rgba_hex(hex_channels) == expected


@pytest.mark.parametrize(
    ("float_channels", "expected"),
    [
        ([1.0, 1.0, 1.0], "#ffffff"),
        ([0.0, 0.0, 0.0], "#000000"),
        ([1.0, 0.5, 0.0], "#ff7f00"),
        ([1.0, 0.5], "#ff7f"),
        ([1.0, 0.5, 0.0, 1.0], "#ff7f00ff"),
    ],
)
def test_float_channels_to_hex(float_channels, expected):
    assert float_channels_to_hex(float_channels) == expected
    if len(float_channels) == 3:
        assert rgb_float_to_hex(float_channels) == expected


@pytest.mark.parametrize(
    ("hex_channels", "expected"),
    [
        ("#ffffff", [1.0, 1.0, 1.0]),
        ("#000000", [0.0, 0.0, 0.0]),
        ("#ff7f00", [1.0, 0.4980392156862745, 0.0]),
        ("#ff7f", [1.0, 0.4980392156862745]),
        ("#ff7f00ff", [1.0, 0.4980392156862745, 0.0, 1.0]),
    ],
)
def test_hex_to_float_channels(hex_channels, expected):
    assert pytest.approx(hex_to_float_channels(hex_channels)) == expected
    if len(expected) == 3:
        assert pytest.approx(hex_to_rgb_float(hex_channels)) == expected


@pytest.mark.parametrize(
    "invalid_input",
    [
        [],
        [1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
    ],
)
def test_rgb_float_to_hex_raises_if_invalid_number_of_input_channels(invalid_input):
    with pytest.raises(AssertionError):
        rgb_float_to_hex(invalid_input)


@pytest.mark.parametrize(
    "invalid_input",
    [
        "#fff",
        "#ff7f00ff",
        "#ff",
        "abc",
    ],
)
def test_hex_to_rgb_float_raises_if_hex_len_is_incorrect(invalid_input):
    with pytest.raises(AssertionError):
        hex_to_rgb_float(invalid_input)
