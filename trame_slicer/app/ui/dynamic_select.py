from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VSelect


@dataclass
class DynamicSelectState:
    current_id: int = -1
    items: list[dict[str, int | str]] = field(default_factory=list)


class DynamicSelect(VSelect):
    def __init__(self, state: TypedState[DynamicSelectState], **kwargs):
        super().__init__(
            v_model=state.name.current_id,
            items=(state.name.items,),
            item_value="id",
            item_title="title",
            hide_details=True,
            density="compact",
            **kwargs,
        )
