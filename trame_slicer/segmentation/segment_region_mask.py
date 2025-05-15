from __future__ import annotations

import enum
from enum import auto

import numpy as np
from numpy.typing import NDArray

from .segmentation import Segmentation


class MaskedRegion(enum.Flag):
    # Overwrite everywhere without restrictions (default)
    EveryWhere = auto()

    # Modifiers to be used with segments options
    VisibleOnly = auto()
    AllSegments = auto()
    SelectedSegmentsOnly = auto()

    # Modify inside / outside segments (all / selected)
    InsideSegments = auto()
    OutsideSegments = auto()

    InsideAllSegments = InsideSegments | AllSegments
    OutsideAllSegments = OutsideSegments | AllSegments

    InsideAllVisibleSegments = InsideSegments | AllSegments | VisibleOnly
    OutsideAllVisibleSegments = OutsideSegments | AllSegments | VisibleOnly

    InsideSelectedSegments = InsideSegments | SelectedSegmentsOnly
    OutsideSelectedSegments = OutsideSegments | SelectedSegmentsOnly


class SegmentRegionMask:
    """
    Helper class for generating an appropriate mask given input masked regions and selected segments.
    """

    def __init__(
        self,
        segmentation: Segmentation,
        masked_region: MaskedRegion = MaskedRegion.EveryWhere,
    ):
        self._segmentation = segmentation
        self.masked_region = masked_region
        self.selected_ids = []

    def get_masked_region(self, labelmap: NDArray) -> NDArray:
        if self.masked_region == MaskedRegion.EveryWhere:
            return np.ones_like(labelmap, dtype=bool)

        segment_mask = self.get_segment_mask(labelmap)
        if self.masked_region & MaskedRegion.InsideSegments:
            return segment_mask
        return ~segment_mask

    def get_segment_mask(self, labelmap: NDArray) -> NDArray:
        segment_ids = self.selected_ids
        if not segment_ids or self.masked_region & MaskedRegion.AllSegments:
            segment_ids = self._segmentation.get_segment_ids()

        if self.masked_region & MaskedRegion.VisibleOnly:
            segment_ids = list(set(segment_ids) & set(self._segmentation.get_visible_segment_ids()))

        segment_values = [self._segmentation.get_segment_value(segment_id) for segment_id in segment_ids]
        return np.isin(labelmap, segment_values)
