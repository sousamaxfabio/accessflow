import pytest
from pydantic import ValidationError

from app.config import Settings


def test_github_settings_have_safe_defaults():
    settings = Settings(_env_file=None)

    assert settings.github_api_url == "https://api.github.com"
    assert settings.github_api_version == "2026-03-10"
    assert settings.github_token is None
    assert settings.github_timeout_seconds == 5.0
    assert settings.github_max_retries == 2
    assert settings.github_retry_base_seconds == 0.25
    assert settings.github_max_pages == 5


def test_github_token_is_masked_but_remains_accessible():
    settings = Settings(
        _env_file=None,
        github_token="test-secret-token",
    )

    assert str(settings.github_token) == "**********"
    assert settings.github_token.get_secret_value() == "test-secret-token"


def test_invalid_github_timeout_is_rejected():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            github_timeout_seconds=0,
        )
