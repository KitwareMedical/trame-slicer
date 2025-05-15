from __future__ import annotations

import re


def _to_camel_case(attr: str) -> str:
    """
    Copied from https://github.com/jpvanhal/inflection/blob/master/inflection/__init__.py
    """
    return re.sub(r"(?:^|_)(.)", lambda m: m.group(1).upper(), attr)


def _to_snake_case(attr: str) -> str:
    """
    Copied from https://github.com/jpvanhal/inflection/blob/master/inflection/__init__.py
    """
    attr = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", attr)
    attr = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", attr)
    attr = attr.replace("-", "_")
    return attr.lower()


class SlicerWrappingAttributeError(AttributeError):
    pass


class SlicerWrapper:
    """
    This class provides automatic conversion of snake_case attributes to CamelCase if
    the original attribute is not found in any slicer object. If neither form exists,
    raises AttributeError is raised.

    Delegates calls to the wrapped object.
    """

    def __init__(self, slicer_obj: object | None = None):
        self._slicer_obj = None
        self.set_wrapped_obj(slicer_obj)

    def set_wrapped_obj(self, slicer_obj: object | None):
        self._slicer_obj = slicer_obj

    def __getattribute__(self, attr: str):
        """
        Returns attribute contained in wrapped objects, if the wrapped objects contain the attribute.
        :raise AttributeError: If attribute is not contained in any wrapped object.
        """
        class_name = type(self).__name__

        try:
            return super().__getattribute__(attr)
        except SlicerWrappingAttributeError as e:
            # If attribute is present in the class but raised because of the wrapping, inform of the error
            _error_msg = (
                f"Failed to access attribute '{attr}' of class '{class_name}' due to the following error : {e}."
            )
            if self._slicer_obj is None:
                _error_msg += " This error is likely due to the wrapped Slicer object being None."
            raise AttributeError(_error_msg) from e
        except AttributeError:
            # Return slicer attr if present either in snake_case or CamelCaseCase
            attr_names = {attr, _to_camel_case(attr)}

            for attr_name in attr_names:
                try:
                    return getattr(self._slicer_obj, attr_name)
                except AttributeError:
                    pass

            # Raise error otherwise
            _attr_msg = " or ".join([f"'{attr_name}'" for attr_name in attr_names])
            _error_msg = f"Type '{class_name}' does not contain attribute {_attr_msg}."
            raise SlicerWrappingAttributeError(_error_msg) from None

    def __dir__(self):
        """Return all attributes for IDE autocompletion"""
        slicer_obj_dir = dir(self._slicer_obj) + list(map(_to_snake_case, dir(self._slicer_obj)))
        self_dir = list(self.__dict__) + list(dir(type(self)))
        return self_dir + slicer_obj_dir


def wrap(obj):
    return SlicerWrapper(obj)
