from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique

from .abstract_view import ViewOrientation, ViewProps


@unique
class ViewType(Enum):
    SLICE_VIEW = "vtkMRMLSliceNode"
    THREE_D_VIEW = "vtkMRMLViewNode"


@dataclass
class ViewLayoutDefinition:
    singleton_tag: str
    view_type: Enum
    properties: ViewProps

    def to_xml(self):
        return f'<view class="{self.view_type.value}" singletontag="{self.singleton_tag}">{self.properties.to_xml()}</view>'

    @classmethod
    def from_xml(cls, xml_str: str, view_type_cls: type[Enum] | None = None) -> ViewLayoutDefinition:
        from lxml import etree

        view_type_cls = view_type_cls or ViewType
        elt = etree.fromstring(xml_str)

        properties = {child.get("name"): child.text for child in elt.getchildren()}
        return cls(
            singleton_tag=elt.get("singletontag"),
            view_type=view_type_cls(elt.get("class")),
            properties=ViewProps.from_xml_dict(properties),
        )

    @classmethod
    def slice_view(cls, orientation: ViewOrientation, *, label: str | None = None) -> ViewLayoutDefinition:
        label = str(label or orientation)

        return cls(
            singleton_tag=label,
            view_type=ViewType.SLICE_VIEW,
            properties=ViewProps(orientation=orientation, label=label),
        )

    @classmethod
    def axial_view(cls, label: str | None = None) -> ViewLayoutDefinition:
        return cls.slice_view("Axial", label=label or "Red")

    @classmethod
    def coronal_view(cls, label: str | None = None) -> ViewLayoutDefinition:
        return cls.slice_view("Coronal", label=label or "Green")

    @classmethod
    def sagittal_view(cls, label: str | None = None) -> ViewLayoutDefinition:
        return cls.slice_view("Sagittal", label=label or "Yellow")

    @classmethod
    def threed_view(
        cls,
        *,
        name: str = "ThreeD",
        label: str = "1",
        background_color: str | tuple[str, str] = ("#1f2020", "#3c3c3c"),
        box_visible: bool = False,
    ):
        return cls(
            name,
            ViewType.THREE_D_VIEW,
            ViewProps(
                label=label,
                background_color=background_color,
                box_visible=box_visible,
            ),
        )
