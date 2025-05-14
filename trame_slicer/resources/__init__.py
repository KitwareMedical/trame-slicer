from __future__ import annotations

from pathlib import Path

from trame.assets.local import LocalFileManager

from trame_slicer.core import VolumeRendering


def resources_path() -> Path:
    return Path(__file__).parent


def get_terminologies_path() -> Path:
    return resources_path() / "terminologies"


def get_volume_rendering_presets_icon_url(
    icons_folder: str | Path,
    volume_rendering: VolumeRendering,
    icon_ext: str = ".png",
) -> list[tuple[str, str]]:
    """
    Helper method listing the volume rendering presets icons in a given folder and
    returning them in a trame compatible format.
    The name of the icons is expected to match the name of the presets present in
    the loaded VolumeRendering presets.

    :returns: List of tuple with preset name and base 64 encoded image
    """
    icons_folder = Path(icons_folder)
    local_asset = LocalFileManager(icons_folder.resolve().as_posix())

    presets = [(name, f"{name}{icon_ext}") for name in volume_rendering.preset_names()]
    return [
        (name, local_asset.url(name, preset_path))
        for name, preset_path in presets
        if icons_folder.joinpath(preset_path).is_file()
    ]


__all__ = [
    "get_terminologies_path",
    "get_volume_rendering_presets_icon_url",
    "resources_path",
]
