import pytest

import examples.minimal as min_examples
from tests import smoke_test_trame_app


def min_example_apps() -> list[type]:
    import inspect

    return [obj for name, obj in inspect.getmembers(min_examples, inspect.isclass)]


@pytest.mark.parametrize("example_cls", [*min_example_apps()])
@pytest.mark.asyncio
async def test_minimal_example_app_can_be_loaded(async_server, a_server_port, example_cls):
    await smoke_test_trame_app(async_server, a_server_port, example_cls)


def test_serverless_example_can_be_loaded(render_interactive):
    min_examples.server_less_viewer(is_interactive=bool(render_interactive))
