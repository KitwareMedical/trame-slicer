from trame.app import TrameApp

from trame_slicer.app.logic import MedicalViewerLogic
from trame_slicer.app.ui import MedicalViewerUI
from trame_slicer.core import SlicerApp


class MedicalViewerApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)
        self._slicer_app = SlicerApp()
        self._logic = MedicalViewerLogic(self.server, self._slicer_app)
        self._ui = MedicalViewerUI(self.server, self._logic.layout_manager)
        self._logic.set_ui(self._ui)


def main(server=None, **kwargs):
    app = MedicalViewerApp(server)
    app.server.start(**kwargs)


if __name__ == "__main__":
    main()
