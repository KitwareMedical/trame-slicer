from __future__ import annotations

from enum import Enum

from slicer import vtkMRMLSegmentEditorNode


class SegmentationOverwriteMode(Enum):
    OVERWRITE_ALL = vtkMRMLSegmentEditorNode.OverwriteAllSegments
    OVERWRITE_ALL_VISIBLE_SEGMENTS = vtkMRMLSegmentEditorNode.OverwriteVisibleSegments
    ALLOW_OVERLAP = vtkMRMLSegmentEditorNode.OverwriteNone
