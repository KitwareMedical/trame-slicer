from __future__ import annotations

from enum import Enum
from functools import lru_cache

from vtkmodules.vtkRenderingCore import (
    VTK_CURSOR_ARROW,
    VTK_CURSOR_CROSSHAIR,
    VTK_CURSOR_HAND,
    VTK_CURSOR_SIZEALL,
    VTK_CURSOR_SIZENE,
    VTK_CURSOR_SIZENS,
    VTK_CURSOR_SIZENW,
    VTK_CURSOR_SIZESE,
    VTK_CURSOR_SIZESW,
    VTK_CURSOR_SIZEWE,
)


class CursorId(Enum):
    """
    Helper ENUM to map between trame and VTK cursor Ids
    """

    AUTO = "auto"
    DEFAULT = "default"
    NONE = "none"
    CONTEXT_MENU = "context-menu"
    HELP = "help"
    POINTER = "pointer"
    PROGRESS = "progress"
    WAIT = "wait"
    CELL = "cell"
    CROSSHAIR = "crosshair"
    TEXT = "text"
    VERTICAL_TEXT = "vertical-text"
    ALIAS = "alias"
    COPY = "copy"
    MOVE = "move"
    NO_DROP = "no-drop"
    NOT_ALLOWED = "not-allowed"
    GRAB = "grab"
    GRABBING = "grabbing"
    E_RESIZE = "e-resize"
    N_RESIZE = "n-resize"
    NE_RESIZE = "ne-resize"
    NW_RESIZE = "nw-resize"
    S_RESIZE = "s-resize"
    SE_RESIZE = "se-resize"
    SW_RESIZE = "sw-resize"
    W_RESIZE = "w-resize"
    EW_RESIZE = "ew-resize"
    NS_RESIZE = "ns-resize"
    NESW_RESIZE = "nesw-resize"
    NWSE_RESIZE = "nwse-resize"
    COL_RESIZE = "col-resize"
    ROW_RESIZE = "row-resize"
    ALL_SCROLL = "all-scroll"
    ZOOM_IN = "zoom-in"
    ZOOM_OUT = "zoom-out"

    @classmethod
    @lru_cache
    def from_vtk_cursor_id(cls, vtk_cursor: int) -> CursorId:
        """
        VTK cursor int to cursor enum.
        """

        return {
            VTK_CURSOR_ARROW: cls.DEFAULT,
            VTK_CURSOR_SIZENE: cls.NE_RESIZE,
            VTK_CURSOR_SIZENW: cls.NW_RESIZE,
            VTK_CURSOR_SIZESW: cls.SW_RESIZE,
            VTK_CURSOR_SIZESE: cls.SE_RESIZE,
            VTK_CURSOR_SIZENS: cls.NS_RESIZE,
            VTK_CURSOR_SIZEWE: cls.EW_RESIZE,
            VTK_CURSOR_SIZEALL: cls.ALL_SCROLL,
            VTK_CURSOR_HAND: cls.POINTER,
            VTK_CURSOR_CROSSHAIR: cls.CROSSHAIR,
        }.get(vtk_cursor, cls.AUTO)
