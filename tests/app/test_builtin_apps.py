import pytest

from tests import smoke_test_trame_app
from trame_slicer.app import MedicalViewerApp, SegmentationApp


@pytest.mark.parametrize("builtin_cls", [MedicalViewerApp, SegmentationApp])
@pytest.mark.asyncio
async def test_builtin_app_can_be_loaded(async_server, a_server_port, builtin_cls):
    await smoke_test_trame_app(async_server, a_server_port, builtin_cls)
