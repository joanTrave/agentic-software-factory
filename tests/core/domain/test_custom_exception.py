from src.core.domain.exceptions.custom_exception import (
    CustomException,
    CustomNotFoundException,
)


def test_custom_exception_sets_message_and_reason():
    exc = CustomException("Something went wrong.", "somethingWentWrong")

    assert exc.message == "Something went wrong."
    assert exc.reason == "somethingWentWrong"


def test_custom_exception_str_returns_message():
    exc = CustomException("Something went wrong.", "somethingWentWrong")

    assert str(exc) == "Something went wrong."


def test_custom_not_found_exception_builds_message_and_reason():
    exc = CustomNotFoundException("Pokemon", "7")

    assert exc.message == "Pokemon with ID 7 not found."
    assert exc.reason == "pokemonNotFound"


def test_custom_not_found_exception_lower_cases_only_first_character_of_entity_name():
    exc = CustomNotFoundException("CompanyLiquidation", "42")

    assert exc.message == "CompanyLiquidation with ID 42 not found."
    assert exc.reason == "companyLiquidationNotFound"


def test_custom_not_found_exception_is_a_custom_exception():
    exc = CustomNotFoundException("Pokemon", "7")

    assert isinstance(exc, CustomException)
