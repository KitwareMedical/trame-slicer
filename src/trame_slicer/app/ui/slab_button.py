from dataclasses import dataclass
from enum import Enum

import vtk
from trame_client.widgets.core import Template
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
