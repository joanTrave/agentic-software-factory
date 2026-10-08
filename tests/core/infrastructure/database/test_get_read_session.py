import pytest

from src.core.infrastructure.database.sql import (
    session_manager as session_manager_module,
)
from src.core.infrastructure.database.sql.session_manager import get_read_session


def test_get_read_session_raises_runtime_error_before_configuration(monkeypatch):
    monkeypatch.setattr(session_manager_module, "_session_factory", None)

    with pytest.raises(RuntimeError):
        get_read_session()
