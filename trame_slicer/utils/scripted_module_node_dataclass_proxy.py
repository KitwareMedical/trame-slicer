import json
from dataclasses import MISSING, Field
from datetime import date, datetime, time, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import TypeVar
from uuid import UUID

from slicer import vtkMRMLNode, vtkMRMLScene, vtkMRMLScriptedModuleNode
from trame_server.utils.typed_state import (
    CollectionEncoderDecoder,
    IStateEncoderDecoder,
    TypedState,
)

__SCRIPTED_PROXY_SUFFIX = "__ScriptedModuleProxy"


class DefaultScriptedModuleEncoderDecoder(IStateEncoderDecoder):
    """
    Default primitive type encoding/decoding for scripted field.
    """

    def __init__(self, scene: vtkMRMLScene):
        super().__init__()
        self._scene = scene

    def encode(self, obj) -> str:
        if isinstance(obj, str):
            return obj
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.name
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.astimezone(timezone.utc).isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, time):
            return obj.isoformat()
        if isinstance(obj, Path):
            return obj.as_posix()
        if isinstance(obj, vtkMRMLNode):
            return obj.GetID()
        return obj

    def decode(self, obj: str, obj_type: type):
        if obj is None:
            return None
        if isinstance(obj, obj_type):
            return obj
        if issubclass(obj_type, Enum):
            return obj_type[obj]
        if issubclass(obj_type, datetime):
            return obj_type.fromisoformat(obj)
        if issubclass(obj_type, date):
            return obj_type.fromisoformat(obj)
        if issubclass(obj_type, time):
            return obj_type.fromisoformat(obj)
        if issubclass(obj_type, vtkMRMLNode):
            return self._scene.GetNodeByID(obj) if obj else None
        return obj_type(obj)


class _ScriptedProxyField:
    """
    Descriptor for proxy scripted node fields to an equivalent dataclass field.
    If the dataclass provides default, or a default factory, the associated state will be initialized to the given
    encoded state value.

    :param node: Trame State which will be mutated / read from.
    :param state_id: Associated trame string id where the data will be pushed / read from.
    :param name: Name of the source field.
    :param field_type: Type of the source field.
    :param default: Default value of the source field.
    :param default_factory: Default factory of the source field.
    :param state_encoder: Encoder/decoder class for the proxy.
    """

    def __init__(
        self,
        *,
        node: vtkMRMLScriptedModuleNode,
        state_id: str,
        name: str,
        field_type: type,
        default,
        default_factory,
        state_encoder: IStateEncoderDecoder,
    ):
        self._node = node
        self._state_id = state_id
        self._name = name
        self._encoder = state_encoder
        self._type = field_type

        # Set the default value to trame state if needed
        self._default = default
        if self._default == MISSING and default_factory != MISSING:
            self._default = default_factory()

    def __get__(self, instance, owner):
        return self.get_value()

    def __set__(self, instance, value):
        self.set_value(value)

    def get_value(self):
        if self._state_id not in self._node.GetParameterNames():
            return self._default if self._default != MISSING else None

        value = json.loads(self._node.GetParameter(self._state_id))
        return self._encoder.decode(value, self._type)

    def set_value(self, value):
        encoded = json.dumps(self._encoder.encode(value))
        self._node.SetParameter(self._state_id, encoded)


T = TypeVar("T")


def create_scripted_module_dataclass_proxy(
    dataclass_type: type[T],
    node: vtkMRMLScriptedModuleNode,
    scene: vtkMRMLScene,
    encoders: list[IStateEncoderDecoder] | None = None,
) -> T:
    encoder = CollectionEncoderDecoder(encoders or [DefaultScriptedModuleEncoderDecoder(scene)])

    def handler(state_id: str, field: Field, field_type: type):
        return _ScriptedProxyField(
            node=node,
            state_id=state_id,
            name=field.name,
            default=field.default,
            default_factory=field.default_factory,
            field_type=field_type,
            state_encoder=encoder,
        )

    return TypedState._build_proxy_cls(dataclass_type, "", handler, cls_suffix=__SCRIPTED_PROXY_SUFFIX)


def create_scripted_module_dataclass_proxy_name(dataclass_type: type[T]) -> T:
    return TypedState._create_state_names_proxy(dataclass_type)


def is_scripted_module_dataclass(instance: T):
    return TypedState.is_proxy_class(instance) and type(instance).__name__.endswith(__SCRIPTED_PROXY_SUFFIX)


def raise_if_not_scripted_proxy(instance: T):
    if not is_scripted_module_dataclass(instance):
        _error_msg = f"Expected instance of scripted module node proxy. Got: {type(instance).__name__}"
        raise RuntimeError(_error_msg)


def scripted_proxy_from_dataclass(instance: T, dataclass_obj: T) -> T:
    raise_if_not_scripted_proxy(instance)
    return TypedState.from_dataclass(instance, dataclass_obj)


def scripted_proxy_to_dataclass(instance: T) -> T:
    raise_if_not_scripted_proxy(instance)
    return TypedState.as_dataclass(instance)
