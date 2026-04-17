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

## Available Effects

trame-slicer provides several built-in segmentation effects:

- **Paint / Erase**: Brush-based tools to add or remove segmentation.
- **Draw**: Polygon/curve selection tool for 2D slice views.
- **Scissors**: Polygon/curve selection tool for 2D and 3D views with advanced
  fill and range options.
- **Threshold**: Real-time thresholding based on intensity values. Supports
  automatic thresholding using various methods (Otsu, Huang, Triangle, etc.).
- **Smoothing**: Set of tools to reduce noise or fill holes in segments (Median,
  Opening, Closing, Gaussian, and Joint smoothing).
- **Islands**: Tools to manage disconnected regions within segments (Keep
  largest, Remove small, Split to segments, etc.).
- **Logical Operators**: Perform boolean operations between segments (Add,
  Subtract, Intersect, etc.).

## Draw and Scissors Effects

Both Draw and Scissors effects use a polygon/curve selection tool to modify the
segmentation. They share the same underlying interaction logic but differ in
their default configuration and supported views:

- **Draw Effect**: Specifically designed for 2D slice views. It is
  pre-configured to fill inside the drawn contour on the current slice.
- **Scissors Effect**: Works in both 2D and 3D views. It provides more options
  for filling/erasing inside or outside the selection, and can operate across
  multiple slices depending on the range mode.

### Interaction Modes

The Draw and Scissors effects support different interaction modes via the
`BrushInteractionMode` parameter:

- **CONTINUOUS**: The segmentation is created by clicking and dragging the
  mouse. The contour follows the mouse path.
- **POINT_BY_POINT**: The segmentation is created by clicking individual points.
  A preview line connects the last point to the current mouse position. The
  contour is closed by right-clicking.

## Smoothing Effect

The Smoothing effect provides several methods to clean up segmentations:

- **Median**: Reduces noise while preserving edges.
- **Opening**: Removes small protrusions and disconnected points.
- **Closing**: Fills small holes and gaps.
- **Gaussian**: Smoothes edges by applying a Gaussian blur.
- **Joint**: Simultaneously smoothes all visible segments while ensuring they
  remain aligned without overlaps or gaps (based on Taubin's method).

## Islands Effect

The Islands effect allows managing disconnected components (islands) within a
segment:

- **Keep largest island**: Removes all islands except the one with the largest
  volume.
- **Remove small islands**: Deletes all islands smaller than a specified voxel
  count.
- **Split to segments**: Moves each island into a new separate segment.
- **Interactive modes**: Allows adding, removing, or keeping islands by clicking
  on them in the views.

## Logical Operators Effect

The Logical Operators effect performs boolean operations between the active
segment and other segments.

For intersection and subtraction, the ALLOW_OVERLAP segmentation mode needs to
be activated.

- **Add / Subtract / Intersect**: Combines or modifies the active segment using
  another segment as a mask.
- **Invert**: Flips the segmentation (filled areas become empty, empty areas
  become filled).
- **Clear / Fill**: Completely empties or fills the active segment within the
  reference volume extent.
