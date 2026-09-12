import pytest

from tests import smoke_test_trame_app
from trame_slicer.app import MedicalViewerApp, SegmentationApp

BUILTIN_APPS = [MedicalViewerApp, SegmentationApp]


@pytest.mark.parametrize(
    ("builtin_cls", "async_server"),
    [(app_cls, getattr(app_cls, "client_type", "vue3")) for app_cls in BUILTIN_APPS],
    indirect=["async_server"],
)
@pytest.mark.asyncio
async def test_builtin_app_can_be_loaded(async_server, unused_tcp_port, builtin_cls):
    await smoke_test_trame_app(async_server, unused_tcp_port, builtin_cls)
