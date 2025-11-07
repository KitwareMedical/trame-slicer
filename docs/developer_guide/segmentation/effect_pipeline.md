# Segmentation effect pipeline

The segmentation effect pipeline(s) are responsible for displaying visual
feedbacks or provide user interaction features in trame-slicer's render windows
(ie. Slice and 3D views).

```{seealso}
The segmentation effect pipeline relies on
the [SlicerLayerDisplayableManager](https://github.com/KitwareMedical/SlicerLayerDisplayableManager) library for their
inner working and users only need to implement specific VTK pipeline logic for their implementation.
```

## Naming conventions

As the segmentation effect pipeline inherits the vtkMRMLLayerDMScriptedPipeline
which is a C++ VTK wrapping, the VTK naming conventions are kept for these
classes.

## API

Effects pipeline have access to the following attributes :

- GetEffectParameterNode(self): The effect's vtkMRMLScriptedModuleNode
- GetModifier(self): The SegmentModifier responsible for modifying the active
  segmentation
- GetSegmentation(self): The Segmentation instance the effect is applied on
- OnEffectParameterUpdate(self): The callback triggered when the effect's
  parameters have changed
- OnViewModified(self): The callback triggered when the view on which the effect
  is attached is modified
- ProcessInteractionEvent(self, event_data: vtkMRMLInteractionEventData):
  Callback called when the user interacts with the view if the effect pipeline
  is the most appropriate for handling the interaction (function of the
  CanProcessInteractionEvent call)
- CanProcessInteractionEvent(self, eventData: vtkMRMLInteractionEventData):
  Callback called when the user interacts with the view (ie. mouse move events /
  clicks / etc.)
- \_effect: The effect which instantiated the effect pipeline
- \_view: The AbstractView (SliceView / 3D View / ...) in which the effect is
  displayed

## Examples

### Visual feedback

The following snippet provides an example of threshold effect pipeline.

The class inherits the `SegmentationEffectPipeline` base class and overrides its
creator. In its creator, it instantiates a VTK pipeline to display the threshold
area in the 2D views.

The VTK objects are added to the VTK render window in the `OnRendererAdded`
method.

Periodic updates of the display is wrapped in an asyncio task for periodicity.
As this effect only provides a visual feedback, it doesn't need to implement any
interaction method.

Connection to the actual volume and segmentation node are done in the
`OnViewModified` and `_UpdateThreshold` respectively.

Access to the parameters is done using the
`create_scripted_module_dataclass_proxy` method. This helper method allows to
convert a vtkMRMLScriptedModuleNode present in the scene to a dataclass object
instance and simplifies transfer of strongly type parameters between Slicer and
trame. )

```python
class SegmentationThresholdPipeline2D(SegmentationEffectPipeline):
    def __init__(self):
        super().__init__()
        self.lookup_table = vtkLookupTable()
        self.lookup_table.SetRampToLinear()
        self.lookup_table.SetNumberOfTableValues(2)
        self.lookup_table.SetTableRange(0, 1)
        self.lookup_table.SetTableValue(0, 0, 0, 0, 0)
        self.color_mapper = vtkImageMapToRGBA()
        self.color_mapper.SetOutputFormatToRGBA()
        self.color_mapper.SetLookupTable(self.lookup_table)
        self.threshold = vtkImageThreshold()
        self.threshold.SetInValue(1)
        self.threshold.SetOutValue(0)
        self.threshold.SetOutputScalarTypeToUnsignedChar()

        # Feedback actor
        self.mapper = vtkImageMapper()
        self.dummy_image = vtkImageData()
        self.dummy_image.AllocateScalars(VTK_UNSIGNED_INT, 1)
        self.mapper.SetInputData(self.dummy_image)
        self.actor = vtkActor2D()
        self.actor.VisibilityOff()
        self.actor.SetMapper(self.mapper)
        self.mapper.SetColorWindow(255)
        self.mapper.SetColorLevel(128)

        # Setup pipeline
        self.color_mapper.SetInputConnection(self.threshold.GetOutputPort())
        self.mapper.SetInputConnection(self.color_mapper.GetOutputPort())

        # Preview coroutine
        self.preview_update_period_s = 0.1
        self.preview_steps = 10
        self.preview_state = 0
        self.preview_direction = 1
        loop = asyncio.get_event_loop()
        self.preview_task = loop.create_task(self._UpdatePreviewState())

    async def _UpdatePreviewState(self):
        while True:
            await asyncio.sleep(self.preview_update_period_s)
            self.preview_state += self.preview_direction
            if self.preview_state > self.preview_steps or self.preview_state < 0:
                self.preview_direction *= -1
            self.preview_state = max(0, min(self.preview_steps, self.preview_state))
            self._UpdateThreshold()

    def OnRendererAdded(self, renderer: vtkRenderer | None) -> None:
        super().OnRendererAdded(renderer)
        if renderer:
            renderer.AddViewProp(self.actor)

    def OnRendererRemoved(self, renderer: vtkRenderer) -> None:
        super().OnRendererRemoved(renderer)
        if renderer and renderer.HasViewProp(self.actor):
            renderer.RemoveViewProp(self.actor)

    def SetActive(self, isActive: bool):
        super().SetActive(isActive)
        self.actor.SetVisibility(isActive)
        self.RequestRender()

    def OnEffectParameterUpdate(self):
        super().OnEffectParameterUpdate()
        if not self.GetEffectParameterNode():
            return
        self._UpdateThreshold()

    def _UpdateThreshold(self):
        if not self.IsActive():
            return

        param = create_scripted_module_dataclass_proxy(
            ThresholdParameters, self.GetEffectParameterNode(), self.GetScene()
        )

        active_id = self.GetModifier().active_segment_id
        if segmentation := self.GetSegmentation():
            opacity = 0.5 + 0.5 * self.preview_state / self.preview_steps
            r, g, b = segmentation.get_segment_properties(active_id).color
            self.lookup_table.SetTableValue(1, r, g, b, opacity)

        self.threshold.ThresholdBetween(param.min_value, param.max_value)
        self.OnViewModified()
        self.threshold.Update()
        self.RequestRender()

    def SetView(self, view: SliceView):
        if self._view:
            self._view.modified.disconnect(self.OnViewModified)
        super().SetView(view)
        if self._view:
            self._view.modified.connect(self.OnViewModified)

    def OnViewModified(self, *_):
        if not self._view or not self.GetModifier():
            return

        self.threshold.SetInputConnection(
            self._view.get_volume_layer_logic(self.GetModifier().volume_node)
            .GetReslice()
            .GetOutputPort()
        )
```
