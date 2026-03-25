"""
Example of starting a server less viewer with one 3D view in interactive mode
"""

from pathlib import Path

from trame_slicer.core import SlicerApp
from trame_slicer.views import DirectViewFactory, ViewLayoutDefinition


def main(is_interactive: bool = True):
    # Create the Slicer app
    slicer_app = SlicerApp()

    # Define and instantiate a 3D view
    slicer_app.view_manager.register_factory(DirectViewFactory(do_render_offscreen=not is_interactive))
    threed_view = slicer_app.view_manager.create_view(ViewLayoutDefinition.threed_view())

    # Load and display a volume node
    mr_head_path = Path(__file__).parent / ".." / ".." / "tests" / "data" / "mr_head.nrrd"
    volume_node = slicer_app.io_manager.load_volumes(mr_head_path.as_posix())[0]
    slicer_app.display_manager.show_volume(volume_node, vr_preset="MR-Default")

    # Start the VTK render window interactor
    threed_view.update_size(400, 300)
    if is_interactive:
        threed_view.start_interactor()


if __name__ == "__main__":
    main()
