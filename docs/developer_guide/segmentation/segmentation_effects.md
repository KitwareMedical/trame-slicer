# Segmentation Effect Architecture

## Design principle

- The segmentation effects rely on dataclass instances as parameters
- The parameters are mapped automatically to vtkMRMLScriptedModuleNode for
  exchange between the Scene and the segmentation effect.
- The segmentation effect can have any number of direct actions such as apply /
  preview / etc. but should only act if the effect is set active by the
  segmentation editor.
- Effects will only rely on the active modifier which is configured by the
  SegmentationEditor.
- UI should only rely on the segmentation effect Parameter and effect actions.
  The UI should be visible only if the effect is active.
- UI binding will access the active effect API directly to call its actions by
  getting the active effect from the segment editor and calling the method
  directly.
- Parameter binding should rely only on the dataclass and forward trame
  parameters to Slicer parameters using the dedicated proxies.
- Effects can have any number of feedback pipelines and are responsible for
  instantiating them.
