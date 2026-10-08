import asyncio
import json

from starlette.requests import Request

from src.core.domain.exceptions.custom_exception import (
    CustomException,
    CustomNotFoundException,
)
from src.core.infrastructure.api.exception_handlers import custom_exception_handler


def _build_request() -> Request:
    return Request(scope={"type": "http", "headers": []})


def test_exception_handler_returns_404_when_reason_ends_with_not_found():
    exc = CustomNotFoundException("Pokemon", "7")

    response = asyncio.run(custom_exception_handler(_build_request(), exc))

    assert response.status_code == 404
    assert json.loads(response.body) == {
        "detail": "Pokemon with ID 7 not found.",
        "reason": "pokemonNotFound",
    }


def test_exception_handler_returns_400_for_any_other_reason():
    exc = CustomException("Something went wrong.", "somethingWentWrong")

    response = asyncio.run(custom_exception_handler(_build_request(), exc))

    assert response.status_code == 400
    assert json.loads(response.body) == {
        "detail": "Something went wrong.",
        "reason": "somethingWentWrong",
    }
