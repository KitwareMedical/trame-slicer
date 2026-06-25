from trame.app import TrameApp

from trame_slicer.app.logic import SegmentationAppLogic
from trame_slicer.app.ui import SegmentationAppUI
from trame_slicer.core import SlicerApp


class SegmentationApp(TrameApp):
    def __init__(self, server=None, rca_encoder=None):
        super().__init__(server)
        self._slicer_app = SlicerApp()
        self._logic = SegmentationAppLogic(self.server, self._slicer_app, rca_encoder=rca_encoder)
        self._ui = SegmentationAppUI(self.server, self._logic.layout_manager)
        self._logic.set_ui(self._ui)

    @property
    def ui(self):
        return self._ui.layout


def main(server=None, rca_encoder=None, **kwargs):
    app = SegmentationApp(server, rca_encoder)
    app.server.start(**kwargs)


if __name__ == "__main__":
    from fire import Fire

    Fire(main)
