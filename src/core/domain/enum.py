from __future__ import annotations

from enum import StrEnum
from typing import Any


class CustomEnum(StrEnum):
    """Base class for every enum in the project (best_practices.md Pattern 7).

    A `str`-valued enum so instances serialize naturally wherever a plain string is expected
    (JSON bodies, Pydantic `model_dump`), with case-tolerant parsing so a slightly differently
    cased value from an external system (a header, a legacy row) still resolves to the right
    member instead of raising.
    """

    @classmethod
    def _missing_(cls, value: Any) -> CustomEnum | None:
        if isinstance(value, str):
            lowered = value.lower()
            for member in cls:
                if member.value.lower() == lowered:
                    return member
        return None

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]
