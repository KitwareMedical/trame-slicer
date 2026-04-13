from enum import Enum


def enum_to_title(enum: Enum) -> str:
    return enum.name.replace("_", " ").title()
