from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import vtk
from trame_client.widgets.core import Template
from trame_server import Server
from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import (
    VCard,
    VCardText,
    VCheckbox,
    VMenu,
    VRow,
    VSelect,
    VSlider,
)

from trame_slicer.core import SlicerApp

from .control_button import ControlButton


class SlabType(Enum):
    MIN = vtk.VTK_IMAGE_SLAB_MIN
    MAX = vtk.VTK_IMAGE_SLAB_MAX
    AVERAGE = vtk.VTK_IMAGE_SLAB_MEAN
    SUM = vtk.VTK_IMAGE_SLAB_SUM


@dataclass
class SlabState:
    current_slab_type: SlabType = SlabType.MAX
    slab_thickness_value: float = 0.0
    slab_enabled: bool = False


class SlabWidget:
    def __init__(self, server: Server, slicer_app: SlicerApp):
        self._logic = SlabLogic(server, slicer_app)
        self._ui = SlabButton()


class SlabButton(VMenu):
    def __init__(self):
        super().__init__(location="end", close_on_content_click=False)
        typed_state = TypedState(self.state, SlabState)

        with self:
            with Template(v_slot_activator="{ props }"):
                ControlButton(name="Slab Reconstruction", icon="mdi-arrow-collapse-horizontal", v_bind="props")

            with VCard(), VCardText():
                with VRow():
                    VCheckbox(v_model=(typed_state.name.slab_enabled,), label="Slab Reconstruction", hide_details=True)
                with VRow():
                    ControlButton(name="Slab thickness", icon="mdi-arrow-collapse-horizontal", size=32)
                    VSlider(
                        v_model=(typed_state.name.slab_thickness_value,),
                        min=0,
                        max=50,
                        width=250,
                        hide_details=True,
                    )
                with VRow():
                    (
                        VSelect(
                            v_model=(typed_state.name.current_slab_type,),
                            items=(
                                "options",
                                typed_state.encode(
                                    [{"text": st.name.title(), "value": typed_state.encode(st)} for st in SlabType]
                                ),
                            ),
                            item_title="text",
                            item_value="value",
                            label="Type",
                            hide_details=True,
                        ),
                    )


class SlabLogic:
    def __init__(self, server: Server, slicer_app: SlicerApp):
        self._slicer_app = slicer_app
        self.typed_state = TypedState(server.state, SlabState)
        self.typed_state.bind_changes(
            {
                self.typed_state.name.current_slab_type: self.on_current_slab_type_change,
                self.typed_state.name.slab_enabled: self._on_slab_toggled,
                self.typed_state.name.slab_thickness_value: self.on_slab_slider_change,
            }
        )

    def on_slab_slider_change(self, slab_thickness: float):
        for slice_view in self._slicer_app.view_manager.get_slice_views():
            slice_view.set_slab_thickness(slab_thickness)

    def on_current_slab_type_change(self, current_slab_type: SlabType):
        for slice_view in self._slicer_app.view_manager.get_slice_views():
            slice_view.set_slab_type(current_slab_type.value)

    def _on_slab_toggled(self, is_enabled: bool):
        for slice_view in self._slicer_app.view_manager.get_slice_views():
            slice_view.set_slab_enabled(is_enabled)
