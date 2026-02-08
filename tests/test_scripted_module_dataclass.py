import json
from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from enum import Enum, auto
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from slicer import vtkMRMLModelNode, vtkMRMLScene, vtkMRMLScriptedModuleNode

from trame_slicer.utils import (
    create_scripted_module_dataclass_proxy,
    create_scripted_module_dataclass_proxy_name,
)


@dataclass
class Simple:
    a: int
    b: str
    c_default: int = 58


@dataclass
class Composite:
    simple: Simple = field(default_factory=Simple)


@pytest.fixture
def a_scene():
    return vtkMRMLScene()


def test_scripted_proxy_can_read_write_from_node(a_scene):
    node = vtkMRMLScriptedModuleNode()
    proxy = create_scripted_module_dataclass_proxy(Simple, node, a_scene)
    name = create_scripted_module_dataclass_proxy_name(Simple)

    proxy.a = 42
    proxy.b = "a string"

    assert node.GetParameter(name.a) == "42"
    assert node.GetParameter(name.b) == '"a string"'

    assert proxy.a == 42
    assert proxy.b == "a string"


def test_accessing_unset_returns_none(a_scene):
    node = vtkMRMLScriptedModuleNode()
    proxy = create_scripted_module_dataclass_proxy(Simple, node, a_scene)
    assert proxy.a is None


def test_accessing_default_unset_returns_default(a_scene):
    node = vtkMRMLScriptedModuleNode()
    proxy = create_scripted_module_dataclass_proxy(Simple, node, a_scene)
    assert proxy.c_default == 58


def test_accessing_default_set_returns_set_value(a_scene):
    node = vtkMRMLScriptedModuleNode()
    name = create_scripted_module_dataclass_proxy_name(Simple)

    node.SetParameter(name.c_default, json.dumps("808"))

    proxy = create_scripted_module_dataclass_proxy(Simple, node, a_scene)
    assert proxy.c_default == 808


def test_scripted_proxy_is_compatible_with_composite(a_scene):
    node = vtkMRMLScriptedModuleNode()
    proxy = create_scripted_module_dataclass_proxy(Composite, node, a_scene)
    name = create_scripted_module_dataclass_proxy_name(Composite)

    proxy.simple.a = 42
    assert node.GetParameter(name.simple.a) == "42"


class MyEnum(Enum):
    A = auto()
    B = auto()
    C = auto()


@dataclass
class DataWithTypes:
    my_enum: MyEnum
    my_uuid: UUID
    my_enum_tuple: tuple[MyEnum]
    my_enum_list: list[MyEnum]
    my_enum_dict: dict[MyEnum, MyEnum]
    my_datetime: datetime
    my_date: date
    my_time: time
    my_path: Path
    my_model_node: vtkMRMLModelNode


def test_scripted_proxy_is_compatible_with_complex_types(a_scene):
    node = vtkMRMLScriptedModuleNode()

    proxy = create_scripted_module_dataclass_proxy(DataWithTypes, node, a_scene)
    name = create_scripted_module_dataclass_proxy_name(DataWithTypes)

    proxy.my_enum = MyEnum.B
    uuid = uuid4()
    proxy.my_uuid = uuid
    proxy.my_enum_tuple = (MyEnum.A, MyEnum.C)
    proxy.my_enum_list = [MyEnum.A, MyEnum.C]
    proxy.my_enum_dict = {MyEnum.A: MyEnum.B}

    dt = datetime.now(tz=timezone.utc)
    proxy.my_datetime = dt
    proxy.my_date = dt.date()
    proxy.my_time = dt.time()
    proxy.my_path = Path(__file__)
    model_node = a_scene.AddNewNodeByClass("vtkMRMLModelNode")
    proxy.my_model_node = model_node

    assert proxy.my_enum == MyEnum.B
    assert proxy.my_uuid == uuid
    assert proxy.my_enum_tuple == (MyEnum.A, MyEnum.C)
    assert proxy.my_enum_list == [MyEnum.A, MyEnum.C]
    assert proxy.my_enum_dict == {MyEnum.A: MyEnum.B}
    assert proxy.my_datetime == dt
    assert proxy.my_date == dt.date()
    assert proxy.my_time == dt.time()
    assert proxy.my_path == Path(__file__)
    assert proxy.my_model_node == model_node

    assert node.GetParameter(name.my_enum) == json.dumps(MyEnum.B.name)
    assert node.GetParameter(name.my_uuid) == json.dumps(str(uuid))
    assert node.GetParameter(name.my_enum_tuple) == json.dumps((MyEnum.A.name, MyEnum.C.name))
    assert node.GetParameter(name.my_enum_list) == json.dumps([MyEnum.A.name, MyEnum.C.name])
    assert node.GetParameter(name.my_enum_dict) == json.dumps({MyEnum.A.name: MyEnum.B.name})
    assert node.GetParameter(name.my_datetime) == json.dumps(dt.isoformat())
    assert node.GetParameter(name.my_date) == json.dumps(dt.date().isoformat())
    assert node.GetParameter(name.my_time) == json.dumps(dt.time().isoformat())
    assert node.GetParameter(name.my_path) == json.dumps(Path(__file__).as_posix())
    assert node.GetParameter(name.my_model_node) == json.dumps(model_node.GetID())


def test_proxy_over_non_scripted_module_returns_none_value(a_scene):
    node = vtkMRMLModelNode()
    proxy = create_scripted_module_dataclass_proxy(Simple, node, a_scene)
    assert proxy.a is None
    assert proxy.b is None
    assert proxy.c_default is None
