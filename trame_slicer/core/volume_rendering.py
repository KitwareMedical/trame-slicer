from __future__ import annotations

from typing import TYPE_CHECKING

from slicer import (
    vtkMRMLMarkupsROINode,
    vtkMRMLVolumeNode,
    vtkMRMLVolumePropertyNode,
    vtkMRMLVolumeRenderingDisplayNode,
    vtkSlicerCropVolumeLogic,
    vtkSlicerVolumeRenderingLogic,
)

from trame_slicer.utils import SlicerWrapper

from .volume_property import VolumeProperty, VRShiftMode

if TYPE_CHECKING:
    from .slicer_app import SlicerApp


class VolumeRendering(SlicerWrapper[vtkSlicerVolumeRenderingLogic]):
    """
    Simple facade for volume rendering logic.
    """

    def __init__(self, slicer_app: SlicerApp):
        super().__init__(slicer_obj=vtkSlicerVolumeRenderingLogic())
        self._scene = slicer_app.scene
        slicer_app.register_module_logic(self._logic)
        self._crop_logic = slicer_app.register_module_logic(vtkSlicerCropVolumeLogic())
        self._logic.ChangeVolumeRenderingMethod("vtkMRMLGPURayCastVolumeRenderingDisplayNode")

    @property
    def _logic(self) -> vtkSlicerVolumeRenderingLogic:
        return self._slicer_obj

    @property
    def crop_logic(self) -> vtkSlicerCropVolumeLogic:
        return self._crop_logic

    def create_display_node(
        self,
        volume_node: vtkMRMLVolumeNode,
        preset_name: str = "",
    ) -> vtkMRMLVolumeRenderingDisplayNode:
        display = self.get_vr_display_node(volume_node)
        if display:
            return display

        display = self._logic.CreateDefaultVolumeRenderingNodes(volume_node)
        self.apply_preset(display, preset_name)
        volume_node.GetDisplayNode().SetVisibility(True)
        display.SetVisibility(True)
        return display

    def apply_preset(
        self,
        display: vtkMRMLVolumeRenderingDisplayNode | None,
        preset_name: str,
    ):
        if not display:
            return

        display.GetVolumePropertyNode().Copy(self.get_preset_property(preset_name).property_node)

    def set_volume_node_property(self, volume_node: vtkMRMLVolumeNode, property_node: vtkMRMLVolumePropertyNode):
        self.apply_vr_node_property(self.get_vr_display_node(volume_node), property_node)

    @staticmethod
    def apply_vr_node_property(
        display: vtkMRMLVolumeRenderingDisplayNode,
        property_node: vtkMRMLVolumePropertyNode,
    ):
        if not display:
            return

        display.GetVolumePropertyNode().Copy(property_node)

    def get_preset_property(self, preset_name) -> VolumeProperty:
        preset_names = self.preset_names()
        if not preset_names:
            return VolumeProperty(None)

        if preset_name not in preset_names:
            preset_name = preset_names[0]

        return VolumeProperty(self._logic.GetPresetByName(preset_name))

    def get_vr_display_node(
        self,
        volume_node: vtkMRMLVolumeNode,
    ) -> vtkMRMLVolumeRenderingDisplayNode | None:
        return self._logic.GetFirstVolumeRenderingDisplayNode(volume_node)

    def has_vr_display_node(self, volume_node: vtkMRMLVolumeNode) -> bool:
        return self.get_vr_display_node(volume_node) is not None

    def _get_preset_nodes(self) -> list[vtkMRMLVolumePropertyNode]:
        preset_nodes_collection = self._logic.GetPresetsScene().GetNodes()
        return [
            preset_nodes_collection.GetItemAsObject(i_node)
            for i_node in range(preset_nodes_collection.GetNumberOfItems())
        ]

    def preset_names(self) -> list[str]:
        preset_nodes = self._get_preset_nodes()
        return [preset_node.GetName() for preset_node in preset_nodes]

    def get_preset_node(self, preset_name: str) -> vtkMRMLVolumePropertyNode | None:
        preset_nodes = self._get_preset_nodes()
        for i in range(len(preset_nodes)):
            if preset_nodes[i].GetName() == preset_name:
                return preset_nodes[i]
        return None

    def set_absolute_vr_shift_from_preset(
        self,
        volume_node: vtkMRMLVolumeNode,
        preset_name: str | None,
        shift: float,
        shift_mode: VRShiftMode = VRShiftMode.BOTH,
    ) -> None:
        """
        Shift the volume rendering opacity and colors by a given value.
        The shift is a scalar value representing how much the preset should be
        moved compared to a preset default.

        Which

        See also:
            :ref: `set_relative_vr_shift`
        """
        preset_prop = None
        if preset_name is not None:
            preset_prop = self.get_preset_property(preset_name)
        vr_prop = self.get_volume_node_property(volume_node)
        vr_prop.set_vr_shift(
            shift,
            shift_mode,
            preset_prop,
        )

    def set_relative_vr_shift(
        self,
        volume_node: vtkMRMLVolumeNode,
        shift: float,
        shift_mode: VRShiftMode = VRShiftMode.BOTH,
    ) -> None:
        """
        Shift the volume rendering opacity and colors by a given value for the current scalar/opacity values.

        See also:
            :ref: `set_absolute_vr_shift_from_preset`
        """
        self.set_absolute_vr_shift_from_preset(
            volume_node=volume_node,
            shift=shift,
            shift_mode=shift_mode,
            preset_name=None,
        )

    def get_vr_shift_range(self, volume_node: vtkMRMLVolumeNode) -> tuple[float, float]:
        return self.get_volume_node_property(volume_node).get_effective_range()

    def get_preset_vr_shift_range(self, preset_name: str) -> tuple[float, float]:
        return self.get_preset_property(preset_name).get_effective_range()

    def get_volume_node_property(self, volume_node: vtkMRMLVolumeNode) -> VolumeProperty:
        return self._get_vr_volume_property(self.get_vr_display_node(volume_node))

    @classmethod
    def _get_vr_volume_property(cls, vr_display_node: vtkMRMLVolumeRenderingDisplayNode | None) -> VolumeProperty:
        return VolumeProperty(vr_display_node.GetVolumePropertyNode() if vr_display_node else None)

    def set_cropping_enabled(
        self,
        volume_node: vtkMRMLVolumeNode,
        roi_node: vtkMRMLMarkupsROINode | None,
        is_enabled: bool,
    ) -> vtkMRMLMarkupsROINode | None:
        """
        Enable or disable the VR cropping for the input volume node.
        If the volume node doesn't have a cropping ROI node and is_enabled is True, a new ROI node will be initialized
        and encompass the full volume node.

        The ROI Node attached to the display node will be returned.
        """
        display_node = self.get_vr_display_node(volume_node)
        if roi_node is None:
            roi_node = display_node.GetROINode()

        if not is_enabled:
            display_node.CroppingEnabledOff()
            return roi_node

        # If no ROI is provided, initialize a ROI fitting the volume geometry
        if roi_node is None:
            roi_node = self._scene.AddNewNodeByClass("vtkMRMLMarkupsROINode")
            roi_node.GetDisplayNode().SetPropertiesLabelVisibility(False)

            crop_volume_parameters = self._scene.AddNewNodeByClass("vtkMRMLCropVolumeParametersNode")
            crop_volume_parameters.SetInputVolumeNodeID(volume_node.GetID())
            crop_volume_parameters.SetROINodeID(roi_node.GetID())
            self._crop_logic.SnapROIToVoxelGrid(crop_volume_parameters)
            self._crop_logic.FitROIToInputVolume(crop_volume_parameters)
            self._scene.RemoveNode(crop_volume_parameters)

        # Set the ROI to the display node and activate it
        display_node.SetAndObserveROINodeID(roi_node.GetID())
        display_node.CroppingEnabledOn()
        return roi_node

    def get_cropping_roi_node(self, volume_node: vtkMRMLVolumeNode | None) -> vtkMRMLMarkupsROINode | None:
        """
        Returns the ROI node instance attached to the input volume node's VR display node if any.
        """
        if not volume_node:
            return None
        display_node = self.get_vr_display_node(volume_node)
        return display_node.GetROINode() if display_node is not None else None

    def get_cropping_roi_visiblity(self, volume_node: vtkMRMLVolumeNode | None) -> bool:
        """
        Returns the input volume node's VR crop ROI node's visibility.
        If the input volume node doesn't have a ROI node, returns False.
        """
        roi_node = self.get_cropping_roi_node(volume_node)
        if not roi_node:
            return False
        return roi_node.GetDisplayVisibility()

    def set_cropping_roi_node_visibile(self, volume_node: vtkMRMLVolumeNode | None, is_visible: bool) -> bool:
        """
        Sets the inputs volume node's VR cropping ROI visible.
        If the input volume node doesn't have a cropping node, does nothgin.

        :return visibility state of the ROI node
        """

        roi_node = self.get_cropping_roi_node(volume_node)
        if not roi_node:
            return False
        roi_node.SetDisplayVisibility(is_visible)
        return is_visible

    def toggle_cropping_visibility(self, volume_node: vtkMRMLVolumeNode | None) -> bool:
        """
        Toggle input volume node cropping visibility.
        Toggling the visibility will activate and initialize the cropping ROI Node if needed.

        :return: New visibility state of the Cropping ROI Node
        """
        if not volume_node:
            return False

        is_visible = not self.get_cropping_roi_visiblity(volume_node)
        return self.set_cropping_roi_node_visibile(volume_node, is_visible)

    def set_vr_opacity(self, volume_node: vtkMRMLVolumeNode, opacity: float, gradient_threshold_hu: float = 0):
        """
        Update volume node gradient opacity function applied on RBG value.
        Copied from :
            https://slicer.readthedocs.io/en/latest/developer_guide/script_repository.html#show-volume-rendering-making-soft-tissues-transparent

        Updates the Volume property node gradient opacity with 0 opacity below a given HU value and the updated slider
        position opacity value above.

        By default, the gradient threshold is set to around water HU value
            https://www.sciencedirect.com/topics/medicine-and-dentistry/hounsfield-scale

        :param volume_node: volume node on which the VR opacity will be applied
        :param opacity: Opacity value between [0, 1]. 1 = fully opaque, 0 = fully transparent.
        :param gradient_threshold_hu: Cut off for opacity gradient.
        """

        if not volume_node:
            return

        volume_display_node = self.get_vr_display_node(volume_node)
        if not volume_display_node:
            return

        opacity_f = volume_display_node.GetVolumePropertyNode().GetGradientOpacity()
        opacity_f.RemoveAllPoints()
        opacity_f.AddPoint(gradient_threshold_hu - 1000, 0.0)
        opacity_f.AddPoint(gradient_threshold_hu, 0)
        opacity_f.AddPoint(gradient_threshold_hu + 1, opacity)
        volume_display_node.SetVisibility(opacity >= 0.01)
