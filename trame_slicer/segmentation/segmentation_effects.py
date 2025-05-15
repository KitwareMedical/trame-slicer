from __future__ import annotations

from enum import IntEnum, auto

from trame_slicer.views import AbstractView, SliceView, ThreeDView

from .segment_modifier import ModificationMode, SegmentModifier
from .segment_paint_widget import (
    BrushModel,
    BrushShape,
    SegmentPaintWidget,
    SegmentPaintWidgetInteractor,
)
from .segment_paint_widget_2d import (
    SegmentPaintWidget2D,
    SegmentPaintWidget2DInteractor,
)
from .segment_paint_widget_3d import (
    SegmentPaintWidget3D,
    SegmentPaintWidget3DInteractor,
)
from .segment_region_mask import MaskedRegion
from .segment_scissor_widget import SegmentScissorWidget, SegmentScissorWidgetInteractor


class SegmentationEffectID(IntEnum):
    NoTool = auto()
    Paint = auto()
    Erase = auto()
    Scissors = auto()


class SegmentationEffect:
    def __init__(self, modifier: SegmentModifier, mode: ModificationMode) -> None:
        self._modifier = modifier
        self._modifier.modification_mode = mode

    def class_name(self):
        return self.__class__.__name__

    def activate(self, views: list[AbstractView]) -> None:
        pass

    def deactivate(self) -> None:
        pass

    def set_masked_region(self, masked_region: MaskedRegion):
        self._modifier.masked_region = masked_region


class _SegmentationPaintEraseEffect(SegmentationEffect):
    def __init__(self, modifier: SegmentModifier, mode: ModificationMode) -> None:
        super().__init__(modifier, mode)
        self._brush_model = BrushModel(BrushShape.Sphere)
        self._interactors: dict[ThreeDView | SliceView, SegmentPaintWidgetInteractor] = {}

    @property
    def brush_size_pix(self) -> float:
        raise NotImplementedError()

    @brush_size_pix.setter
    def brush_size_pix(self, value) -> None:
        raise NotImplementedError()

    @property
    def brush_size_mm(self) -> float:
        raise NotImplementedError()

    @brush_size_mm.setter
    def brush_size_mm(self, value: float) -> None:
        raise NotImplementedError()

    @property
    def brush_shape(self) -> BrushShape:
        raise NotImplementedError()

    @brush_shape.setter
    def brush_shape(self, shape: BrushShape) -> None:
        raise NotImplementedError()

    def get_widgets(self) -> list[SegmentPaintWidget]:
        return [i.widget for i in self._interactors.values()]

    def activate(self, views: list[ThreeDView | SliceView]) -> None:
        for view in views:
            self._interactors[view] = self._create_view_interactor(view)

        self._render_all_views()

    def _create_view_interactor(self, view: SliceView | ThreeDView):
        is_2d_view = isinstance(view, SliceView)
        widget_klass = SegmentPaintWidget2D if is_2d_view else SegmentPaintWidget3D
        interactor_klass = SegmentPaintWidget2DInteractor if is_2d_view else SegmentPaintWidget3DInteractor

        widget = widget_klass(view, self._modifier, self._brush_model)
        interactor = interactor_klass(widget)
        interactor.render_callback = self._render_all_views
        interactor.widget.enable_brush()
        view.add_user_interactor(interactor)
        return interactor

    def deactivate(self) -> None:
        for [view, interactor] in self._interactors.items():
            interactor.widget.disable_brush()
            view.remove_user_interactor(interactor)

        self._render_all_views()
        self._interactors.clear()

    def _render_all_views(self):
        for view in self._interactors:
            view.schedule_render()


class SegmentationPaintEffect(_SegmentationPaintEraseEffect):
    def __init__(self, modifier: SegmentModifier) -> None:
        super().__init__(modifier, ModificationMode.Paint)


class SegmentationEraseEffect(_SegmentationPaintEraseEffect):
    def __init__(self, modifier: SegmentModifier) -> None:
        super().__init__(modifier, ModificationMode.Erase)


class SegmentationScissorEffect(SegmentationEffect):
    def __init__(self, modifier: SegmentModifier) -> None:
        super().__init__(modifier, mode=ModificationMode.EraseAll)
        self._brush_model = BrushModel(BrushShape.Sphere)
        self._widgets: dict[AbstractView, SegmentScissorWidgetInteractor] = {}

    def activate(self, views: list[AbstractView]) -> None:
        for view in [v for v in views if isinstance(v, (ThreeDView | SliceView))]:
            if view not in self._widgets:
                widget = SegmentScissorWidget(view, self._modifier)
                interactor = SegmentScissorWidgetInteractor(widget)
                interactor.render_callback = self._render_all_views
                self._widgets[view] = interactor

            interactor = self._widgets[view]
            interactor.widget.enable_brush()
            view.add_user_interactor(interactor)
            view.schedule_render()

    def deactivate(self) -> None:
        for [_view, interactor] in self._widgets.items():
            interactor.widget.disable_brush()

    def _render_all_views(self):
        for view in self._widgets:
            view.schedule_render()

    def set_mode(self, mode: ModificationMode):
        self._modifier.modification_mode = mode
