import pytest
from pydantic import ValidationError
from app.core.config import Settings


def test_settings_fail_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_database_url_is_hidden_when_printed(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:not-a-real-password@db/securevault")

    settings = Settings(_env_file=None)

    assert "not-a-real-password" not in repr(settings)
    assert settings.database_url.get_secret_value().endswith("@db/securevault")
