from trame.app import TrameApp
from trame.app.testing import enable_testing

try:
    from viewer_lib import SegmentationViewerLogic, SegmentationViewerUI
except ModuleNotFoundError:
    from .viewer_lib import SegmentationViewerLogic, SegmentationViewerUI

from trame_slicer.core import SlicerApp


class SegmentationViewerApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)
        self._slicer_app = SlicerApp()

        self._logic = SegmentationViewerLogic(self._server, self._slicer_app)
        self._ui = SegmentationViewerUI(self._server, self._logic.layout_manager)
        self._logic.set_ui(self._ui)

    @property
    def server(self):
        return self._server


def main(server=None, **kwargs):
    app = SegmentationViewerApp(server)
    enable_testing(app.server)
    app.server.start(**kwargs)


if __name__ == "__main__":
    main()
