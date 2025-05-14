from __future__ import annotations

from dataclasses import asdict, dataclass

import vtk
from slicer import vtkSegment

from trame_slicer.utils import hex_to_rgb_float, rgb_float_to_hex


@dataclass
class SegmentProperties:
    color: list[float]
    name: str
    label_value: int
    terminology_tag: str

    @classmethod
    def from_segment(cls, segment: vtkSegment) -> SegmentProperties | None:
        if segment is None:
            return None

        terminology_tag = vtk.reference("")
        segment.GetTag(segment.GetTerminologyEntryTagName(), terminology_tag)

        return cls(
            color=list(segment.GetColor()),
            label_value=segment.GetLabelValue(),
            name=segment.GetName(),
            terminology_tag=terminology_tag.get(),
        )

    def to_segment(self, segment: vtkSegment):
        if segment is None:
            return

        segment.SetName(self.name)
        segment.SetColor(*self.color)
        segment.SetLabelValue(self.label_value)
        segment.SetTag(segment.GetTerminologyEntryTagName(), self.terminology_tag)

    @property
    def color_hex(self) -> str:
        return rgb_float_to_hex(self.color)

    @color_hex.setter
    def color_hex(self, value: str) -> None:
        self.color = hex_to_rgb_float(value)

    def to_dict(self):
        d = asdict(self)
        d["color_hex"] = self.color_hex
        return d
