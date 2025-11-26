# Design recipes

## Widget implementation

trame-slicer widgets should be cleanly split between UI component and Logic
component to simplify maintenance and allow cross-compatibility of the developed
components between 3D Slicer and trame.

To simplify this cross-compatibility, the UI and logic should rely on :

- dataclasses for parameter handling
- Signal for UI connection

In the trame-slicer environment, the py-undo-stack library is used to provide qt
like Signals. These signals are compatible with any callable connection in the
3D Slicer desktop environment.

### UI decoupling

#### Parameters

By design, trame UI components allow for highly decoupled implementations as all
UI components only require server side state to be defined to be rendered
correctly.

To render UI parameters, the following options are available :

- Define static parameters: this option should be used for static information
  not meant to change during the component's lifetime.
- Define dynamic parameters: this option is used for parameters meant to
  interactively change and be passed from logic to ui. For these parameters, the
  name of the state variable needs to be passed to trame as a tuple entry for
  the reactivity to happen (relies on v-bind internally).

For the later case, parameter binding can be done using trame's TypedState
utility class.

The following code snippet gives an example of a SliderState being coupled to a
VSlider using the Typedstate pattern.

The pattern follows the following steps:

- Define a strongly typed dataclass with default values representing the UI's
  changing data
- Create a UI class deriving from a tram UI component
- Either create locally the typed state using the UI's `self.state` attribute or
  inject the typed state if used in the context of a greater state.
- Connect the UI attributes to trame reactivity using the typed state
  `self.name.<property_name>` and tuple syntax.

```python
from dataclasses import dataclass
from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VRangeSlider, VSlider


@dataclass
class SliderState:
    min_value: float = 0
    max_value: float = 1
    value: float = 0.5
    step: float = 1e-6


class Slider(VSlider):
    def __init__(self, typed_state: TypedState[SliderState], **kwargs):
        super().__init__(
            min=(typed_state.name.min_value,),
            max=(typed_state.name.max_value,),
            v_model=(typed_state.name.value,),
            step=(typed_state.name.step,),
            is_reversed=(typed_state.name.is_reversed,),
            hide_details=True,
            **kwargs,
        )
```

#### Callbacks

For callback decoupling, UI's can use the py-undo-stack's Signal class. The
class provides Qt like Signal implementation.

Here is a simplified example to connect multiple VBtn to the instance's Signal
emitting:

```python
from trame_vuetify.widgets.vuetify3 import VBtn
from undo_stack import Signal


class MyButton(VBtn):
    clicked = Signal()

    def __init__(
        self,
        *,
        name: str,
        icon: str | tuple,
        size: int = 40,
        **kwargs,
    ) -> None:
        size = size or ""
        super().__init__(
            variant="text",
            rounded=0,
            height=size,
            width=size,
            min_height=size,
            min_width=size,
            click=self.clicked,
            **kwargs,
        )


# Connection example
ui = MyButton()
ui.clicked.connect(...)
```

### Logic decoupling

Similarly to the UI decoupling, the logic can use the TypedState pattern to
interact UI changes to logic actions. To do so, the Logic will need either the
trame Server to create a new instance of TypedState or will need a TypedState to
be injected as an input.

The following shows an example of connecting the previous SliderState to a model
opacity change action:

```python
class NodeOpacityLogic:
    def __init__(self, node: vtkMRMLModelNode, typed_state=TypedState[SliderState]):
        self._node = node
        self._typed_state = typed_state

        # The bind_changes method can be used to bind state changes to a given python end point
        self._typed_state.bind_changes(
            {self._typed_state.name.value: self._on_slider_value_changed}
        )

        # The UI can be updated to reflect the current node's opacity
        # (for the example, the node's ModifiedEvent's are not connected)
        self._update_from_mrml()

    def _update_from_mrml(self):
        self._typed_state.data.value = self.node.GetDisplayNode().GetOpacity()

    def _on_slider_value_changed(self, value: float):
        self.node.GetDisplayNode().SetOpacity(value)
```

Signals can be connected directly to the logic method handler.

## Access to 3D Slicer's modules and Scene

To make the UI and Logic compatible with most environments, it is recommended to
clearly set the required dependencies when creating the different classes.

Logic components should not rely on any Qt layer logic, and shouldn't rely on
Singletons.

The following variables are not available when using trame-slider
(non-exhaustive list):

- slicer.mrmlScene
- slicer.app
- slicer.modules
- qt.\*
