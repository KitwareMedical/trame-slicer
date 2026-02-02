from __future__ import annotations

from enum import Flag, auto

from slicer import vtkMRMLSegmentationDisplayNode

from trame_slicer.utils import SlicerWrapper


class SegmentationOpacityEnum(Flag):
    FILL = auto()
    OUTLINE = auto()
    BOTH = FILL | OUTLINE


class SegmentationDisplay(SlicerWrapper[vtkMRMLSegmentationDisplayNode]):
    """
    Wrapper around the segmentation display node.
    """

    def get_border_thickness(self) -> int | None:
        if not self._slicer_obj:
            return None
        return self.GetSliceIntersectionThickness()

    def set_border_thickness(self, thickness: int) -> None:
        if not self._slicer_obj:
            return
        self.SetSliceIntersectionThickness(int(thickness))

    def get_opacity_2d(self) -> float | None:
        if not self._slicer_obj:
            return None
        return self.GetOpacity2DFill()

    def set_opacity_2d(self, opacity: float) -> None:
        if not self._slicer_obj:
            return
        self.SetOpacity2DFill(opacity)
        self.SetOpacity2DOutline(opacity)

    def get_opacity_mode(self) -> SegmentationOpacityEnum | None:
        if not self._slicer_obj:
            return None
        fill_visibility = self.GetVisibility2DFill()
        outline_visibility = self.GetVisibility2DOutline()
        if outline_visibility and not fill_visibility:
            return SegmentationOpacityEnum.OUTLINE
        if fill_visibility and not outline_visibility:
            return SegmentationOpacityEnum.FILL
        return SegmentationOpacityEnum.FILL | SegmentationOpacityEnum.OUTLINE

    def set_opacity_mode(self, opacity_mode: SegmentationOpacityEnum) -> None:
        if not self._slicer_obj:
            return
        self.SetVisibility2DFill(SegmentationOpacityEnum.FILL in opacity_mode)
        self.SetVisibility2DOutline(SegmentationOpacityEnum.OUTLINE in opacity_mode)
