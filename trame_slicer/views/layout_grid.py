from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from itertools import chain
from typing import Protocol, runtime_checkable

from trame.widgets import client, html

from .view_layout_definition import ViewLayoutDefinition


class LayoutDirection(Enum):
    Vertical = auto()
    Horizontal = auto()


@runtime_checkable
class View(Protocol):
    singleton_tag: str


@dataclass
class Layout:
    direction: LayoutDirection
    items: list[Layout | View]
    flex_sizes: list[str] | None = None

    def get_views(self, is_recursive: bool) -> list[View]:
        """
        Returns every views contained in Layout as a flat list.
        :param is_recursive: If true, returns sub layout views as well. Otherwise, returns only direct views.
        """
        views = [item for item in self.items if isinstance(item, View)]
        if not is_recursive:
            return views

        sub_views = list(chain(*[item.get_views(is_recursive) for item in self.items if isinstance(item, Layout)]))
        return views + sub_views

    @classmethod
    def empty_layout(cls):
        return cls(LayoutDirection.Vertical, [])


class LayoutGrid:
    """
    Component responsible for displaying view grids.
    """

    def __init__(
        self,
        layout_items: list[Layout | View],
        layout_direction: LayoutDirection,
        layout_flex_sizes: list[str] | None = None,
    ):
        layout_class = "flex-row" if layout_direction == LayoutDirection.Horizontal else "flex-column"

        with html.Div(
            classes=f"layout-grid-container d-flex {layout_class}",
            style="flex: 1;",
        ):
            for i_item, item in enumerate(layout_items):
                flex_size = (
                    f"{layout_flex_sizes[i_item]}" if layout_flex_sizes and len(layout_flex_sizes) > i_item else "1"
                )

                with html.Div(classes="d-flex", style=f"flex: {flex_size};"):
                    if isinstance(item, Layout):
                        LayoutGrid(item.items, item.direction, item.flex_sizes)
                    else:
                        with html.Div(
                            classes="layout-grid-item",
                            style="display: flex; flex: 1; border: 1px solid #222;",
                        ):
                            client.ServerTemplate(name=item.singleton_tag)

    @classmethod
    def create_root_grid_ui(cls, layout: Layout):
        with html.Div(
            classes="d-flex flex-column flex-grow-1 fill-height",
            style="background-color:black;",
        ):
            cls(layout.items, layout.direction, layout.flex_sizes)


def pretty_xml(xml_str: str) -> str:
    from lxml import etree

    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.XML(xml_str, parser=parser)
    return etree.tostring(root, pretty_print=True).decode()


def vue_layout_to_slicer(layout: Layout):
    layout_str = f'<layout type="{layout.direction.name.lower()}">'

    item: Layout | ViewLayoutDefinition
    for item in layout.items:
        item_xml = vue_layout_to_slicer(item) if isinstance(item, Layout) else item.to_xml()
        layout_str += f"<item>{item_xml}</item>"

    layout_str += "</layout>"
    return layout_str


def slicer_layout_to_vue(xml_str: str) -> Layout:
    from lxml import etree

    elt = etree.fromstring(xml_str)

    def to_layout_item(child):
        _error_msg = "Invalid input XML layout"
        if not child.tag == "item" or len(child.getchildren()) != 1:
            raise RuntimeError(_error_msg)

        child = child.getchildren()[0]
        child_xml_str = etree.tostring(child)
        if child.tag == "layout":
            return slicer_layout_to_vue(child_xml_str)
        if child.tag == "view":
            return ViewLayoutDefinition.from_xml(child_xml_str)

        raise RuntimeError(_error_msg)

    items = [to_layout_item(child) for child in elt.getchildren()]

    return Layout(direction=LayoutDirection[elt.attrib["type"].title()], items=items)
