import json

import pytest
from pydantic import BaseModel

from src.core.domain.enum import CustomEnum


class ColorEnum(CustomEnum):
    RED = "RED"
    GREEN = "GREEN"


class _ColorContainer(BaseModel):
    color: ColorEnum


def test_custom_enum_str_returns_the_value():
    assert str(ColorEnum.RED) == "RED"
    assert str(ColorEnum.GREEN) == "GREEN"


def test_custom_enum_parses_exact_value():
    assert ColorEnum("RED") is ColorEnum.RED


def test_custom_enum_missing_allows_case_tolerant_parsing():
    assert ColorEnum("red") is ColorEnum.RED
    assert ColorEnum("Green") is ColorEnum.GREEN


def test_custom_enum_unknown_value_raises_value_error():
    with pytest.raises(ValueError):
        ColorEnum("purple")


def test_custom_enum_values_lists_members():
    assert set(ColorEnum.values()) == {"RED", "GREEN"}


def test_custom_enum_serializes_to_its_value_in_pydantic_model():
    model = _ColorContainer(color=ColorEnum.RED)

    assert model.model_dump(mode="json")["color"] == "RED"
    assert json.loads(model.model_dump_json())["color"] == "RED"


def test_custom_enum_validates_case_tolerant_value_in_pydantic_model():
    model = _ColorContainer.model_validate({"color": "red"})

    assert model.color is ColorEnum.RED
