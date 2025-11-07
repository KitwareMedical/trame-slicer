# Segmentation Effect Architecture

## Difference with 3D Slicer

trame-slicer segmentation effects are not based on 3D Slicer segmentation
effects as 3D Slicer's effects heavily rely on Qt for their inner workings.

trame-slicer segmentation effects UI interactions are implemented as first class
displayable manager pipelines thanks to the
[SlicerLayerDisplayableManager](https://github.com/KitwareMedical/SlicerLayerDisplayableManager)
library.

## Design principle

- The segmentation effects rely on dataclass instances as parameters
- The parameters are mapped automatically to vtkMRMLScriptedModuleNode for
  exchange between the Scene and the segmentation effect and segmentation effect
  pipelines.
- The segmentation effect can have any number of direct actions such as apply /
  preview / etc. but should only act if the effect is set active by the
  segmentation editor.
- Effects will only rely on the active modifier which is configured by the
  SegmentationEditor.
- UI should only rely on dataclass parameters and effect actions. The UI should
  be visible only if the effect is active. UI parameters and effect parameters
  may be disjoint depending on the use case (for instance when creating
  simplified workflows).
- UI binding will access the active effect API directly to call its actions by
  getting the active effect from the segment editor and calling the method
  directly.
- Effects parameters should be settable from the effect API to simplify
  developer experience. Effect will internally affect the scene parameters.
- Effects can have any number of feedback pipelines and are responsible for
  instantiating them and handling their lifetime.
