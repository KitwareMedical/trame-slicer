from __future__ import annotations

from enum import Enum

from slicer import vtkMRMLSegmentationNode


class SegmentationEditableAreaMode(Enum):
    EVERYWHERE = vtkMRMLSegmentationNode.EditAllowedEverywhere
    INSIDE_SINGLE_SEGMENT = vtkMRMLSegmentationNode.EditAllowedInsideSingleSegment
    INSIDE_ALL_SEGMENTS = vtkMRMLSegmentationNode.EditAllowedInsideAllSegments
    INSIDE_ALL_VISIBLE_SEGMENTS = vtkMRMLSegmentationNode.EditAllowedInsideVisibleSegments
    OUTSIDE_ALL_SEGMENTS = vtkMRMLSegmentationNode.EditAllowedOutsideAllSegments
    OUTSIDE_ALL_VISIBLE_SEGMENTS = vtkMRMLSegmentationNode.EditAllowedOutsideVisibleSegments
