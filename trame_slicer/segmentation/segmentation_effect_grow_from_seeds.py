from __future__ import annotations

from dataclasses import dataclass, field

from slicer import (
    vtkMRMLSegmentationNode,
    vtkOrientedImageData,
)

try:
    import vtkITK
except ModuleNotFoundError:
    from vtkmodules import vtkITK

from ..utils import create_scripted_module_dataclass_proxy
from .paint_effect_parameters import PaintEffectParameters
from .segment_modifier import ModificationMode, SegmentModifier
from .segmentation_display import SegmentationDisplay, SegmentationOpacityEnum
from .segmentation_effect_paint_erase import SegmentationEffectPaintErase


@dataclass
class GrowFromSeedsParameters:
    paint: PaintEffectParameters = field(default_factory=PaintEffectParameters)
    paint_mode: ModificationMode = ModificationMode.Add
    auto_update: bool = False
    preview_node: vtkMRMLSegmentationNode | None = None
    preview_opacity: float = 0.2


class SegmentationEffectGrowFromSeeds(SegmentationEffectPaintErase):
    def __init__(self):
        super().__init__(mode=ModificationMode.Add)
        self._grow_cut_filter = vtkITK.vtkITKGrowCut()
        self._is_outdated = True
        self._preview_modifier: SegmentModifier | None = None

    def _get_grow_from_seeds_parameter(self) -> GrowFromSeedsParameters:
        return create_scripted_module_dataclass_proxy(GrowFromSeedsParameters, self._param_node, self._scene)

    def _get_paint_parameter(self) -> PaintEffectParameters:
        return self._get_grow_from_seeds_parameter().paint

    def update_grow_from_seeds(self) -> None:
        out_label_map = self._modifier.create_modifier_labelmap()

        self._grow_cut_filter.SetIntensityVolume(self._modifier.get_source_image_data())
        self._grow_cut_filter.SetMaskVolume(self._modifier.get_mask_label_map())
        self._grow_cut_filter.SetDistancePenalty(0.0)

        self._grow_cut_filter.SetSeedLabelVolume(self._modifier.get_merged_label_map())
        self._grow_cut_filter.Update()

        out_label_map.DeepCopy(self._grow_cut_filter.GetOutput())
        self._set_preview_segmentation_labelmap(out_label_map)
        self.set_preview_segmentation_visible(True)
        self._is_outdated = False

    def set_active(self, is_active: bool) -> None:
        super().set_active(is_active)
        self._update_preview_segmentation()
        self._update_segmentation_observer()

    def apply_grow_from_seeds(self) -> None:
        if self._is_outdated:
            self.update_grow_from_seeds()

        self._copy_preview_segmentation_to_segmentation()
        self._clear_preview_segmentation()

    def _update_preview_segmentation(self) -> None:
        if not self.is_active:
            self._clear_preview_segmentation()
        else:
            self._initialize_preview_segmentation()

    def _set_preview_segmentation_labelmap(self, label_map: vtkOrientedImageData | None) -> None:
        if not label_map or not self._preview_modifier:
            return

        self._preview_modifier.apply_labelmap(label_map)

    def set_preview_segmentation_visible(self, is_visible: bool) -> None:
        if not self._preview_display:
            return

        self._preview_display.set_visibility(is_visible)

    def set_preview_segmentation_opacity(self, opacity: float) -> None:
        self._get_grow_from_seeds_parameter().preview_opacity = opacity
        self._restore_preview_opacity_from_settings()

    def _restore_preview_opacity_from_settings(self):
        if not self._preview_display:
            return

        self._preview_display.set_opacity_mode(SegmentationOpacityEnum.FILL)
        self._preview_display.set_opacity_2d(self._get_grow_from_seeds_parameter().preview_opacity)

    def _copy_preview_segmentation_to_segmentation(self) -> None:
        if not self._preview_modifier:
            return

        self.set_mode(ModificationMode.Set)
        try:
            self._modifier.apply_labelmap(self._preview_modifier.get_merged_label_map(), is_per_segment=False)
        finally:
            self.set_mode(ModificationMode.Add)

    def _clear_preview_segmentation(self) -> None:
        self._is_outdated = True
        self._scene.RemoveNode(self._preview_modifier.segmentation_node if self._preview_modifier else None)
        self._preview_modifier = None

    def _initialize_preview_segmentation(self) -> None:
        self._clear_preview_segmentation()
        preview_node = self._scene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        preview_node.CreateDefaultDisplayNodes()
        self._preview_modifier = self._modifier.create_new_modifier(preview_node)
        self._preview_modifier.modification_mode = ModificationMode.Set
        self._get_grow_from_seeds_parameter().preview_node = preview_node
        self._restore_preview_opacity_from_settings()

    def _update_segmentation_observer(self) -> None:
        modified_signal = self._modifier.segmentation_modified if self._modifier else None
        if not modified_signal:
            return

        if self.is_active:
            modified_signal.connect(self._on_segmentation_modified)
        else:
            modified_signal.disconnect(self._on_segmentation_modified)

    def _on_segmentation_modified(self):
        self._is_outdated = True
        if self._get_grow_from_seeds_parameter().auto_update:
            self.update_grow_from_seeds()

    @property
    def _preview_display(self) -> SegmentationDisplay | None:
        return (
            self._preview_modifier.segmentation.get_display()
            if (self._preview_modifier and self._preview_modifier.segmentation)
            else None
        )
