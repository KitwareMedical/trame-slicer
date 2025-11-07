from dataclasses import dataclass


@dataclass
class SegmentState:
    name: str = ""
    color: str = ""
    segment_id: str = ""
    is_visible: bool = True
