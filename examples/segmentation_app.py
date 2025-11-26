from trame.app import TrameApp

try:
    from viewer_lib import SegmentationAppLogic, SegmentationAppUI
except ModuleNotFoundError:
    from .viewer_lib import SegmentationAppLogic, SegmentationAppUI

from trame_slicer.core import SlicerApp


class SegmentationApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)
        self._slicer_app = SlicerApp()

        self._logic = SegmentationAppLogic(self.server, self._slicer_app)
        self._ui = SegmentationAppUI(self.server, self._logic.layout_manager)
        self._logic.set_ui(self._ui)


def main(server=None, **kwargs):
    app = SegmentationApp(server)
    app.server.start(**kwargs)


if __name__ == "__main__":
    main()
