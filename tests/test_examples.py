import pytest

import examples.minimal as min_examples
from tests import smoke_test_trame_app


def min_example_apps() -> list[type]:
    import inspect

    return [obj for name, obj in inspect.getmembers(min_examples, inspect.isclass)]


@pytest.mark.parametrize(
    ("example_cls", "async_server"),
    [(app_cls, getattr(app_cls, "client_type", "vue3")) for app_cls in min_example_apps()],
    indirect=["async_server"],
)
@pytest.mark.asyncio
async def test_minimal_example_app_can_be_loaded(async_server, unused_tcp_port, example_cls):
    await smoke_test_trame_app(async_server, unused_tcp_port, example_cls)


def test_serverless_example_can_be_loaded(render_interactive):
    min_examples.server_less_viewer(is_interactive=bool(render_interactive))
