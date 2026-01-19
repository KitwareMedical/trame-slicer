from dataclasses import dataclass

from trame.widgets import vuetify3 as vuetify
from trame_server.utils.typed_state import TypedState

from trame_slicer.segmentation.segmentation_effect_scissors_widget import (
    ScissorsSegmentationOperation,
    ScissorsSegmentationSliceCut,
)

from ..flex_container import FlexContainer


@dataclass
class ScissorsEffectState:
    operation: ScissorsSegmentationOperation = ScissorsSegmentationOperation.ERASE_INSIDE
    cut_mode: ScissorsSegmentationSliceCut = ScissorsSegmentationSliceCut.UNLIMITED
    symmetric_distance: float = 0


class ScissorsEffectUI(FlexContainer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typed_state = TypedState(self.state, ScissorsEffectState)

        self.operations = {
            ScissorsSegmentationOperation.ERASE_INSIDE: "Erase Inside",
            ScissorsSegmentationOperation.ERASE_OUTSIDE: "Erase Outside",
            ScissorsSegmentationOperation.FILL_INSIDE: "Fill Inside",
            ScissorsSegmentationOperation.FILL_OUTSIDE: "Fill Outside",
        }

        self.cut_modes = {
            ScissorsSegmentationSliceCut.UNLIMITED: "Unlimited",
            ScissorsSegmentationSliceCut.POSITIVE: "Positive",
            ScissorsSegmentationSliceCut.NEGATIVE: "Negative",
            ScissorsSegmentationSliceCut.SYMMETRIC: "Symmetric",
        }

        with self:
            with vuetify.VRow():
                with (
                    vuetify.VCol(),
                    vuetify.VRadioGroup(v_model=self._typed_state.name.operation, label="Operation"),
                ):
                    temp = self._typed_state.encode(
                        [
                            {
                                "text": text,
                                "value": value,
                            }
                            for value, text in self.operations.items()
                        ]
                    )
                    vuetify.VRadio(
                        v_for=f"operation in {temp}",
                        label=("operation.text",),
                        value=("operation.value",),
                    )

                with (
                    vuetify.VCol(),
                    vuetify.VRadioGroup(v_model=self._typed_state.name.cut_mode, label="Cut mode"),
                ):
                    temp = self._typed_state.encode(
                        [
                            {
                                "text": text,
                                "value": value,
                            }
                            for value, text in self.cut_modes.items()
                        ]
                    )
                    vuetify.VRadio(
                        v_for=f"operation in {temp}",
                        label=("operation.text",),
                        value=("operation.value",),
                    )
            with vuetify.VRow():
                vuetify.VNumberInput(
                    v_model=self._typed_state.name.symmetric_distance,
                    label="Distance (mm)",
                    disabled=(
                        f"{self._typed_state.name.cut_mode} !== {self._typed_state.encode(ScissorsSegmentationSliceCut.SYMMETRIC)}",
                    ),
                    min=0,
                    max=9999,
                    step=(0.0001,),
                    precision=4,
                    density="comfortable",
                    control_variant="stacked",
                    hide_details=True,
                )
