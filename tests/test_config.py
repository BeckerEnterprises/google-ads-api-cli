"""Tests fuer die Config-Precedence: CLI-Flags > Env-Vars > Config-Datei."""

from __future__ import annotations

import pytest

from googleadscli import config


def test_env_vars_override_config_file(tmp_path, monkeypatch):
    config_file = tmp_path / "google-ads.yaml"
    config_file.write_text(
        "developer_token: from_file\n"
        "client_id: from_file\n"
        "client_secret: from_file\n"
        "refresh_token: from_file\n"
    )
    monkeypatch.setenv("GOOGLE_ADS_DEVELOPER_TOKEN", "from_env")

    merged = config.load_merged_config(config_path=str(config_file))

    assert merged["developer_token"] == "from_env"
    assert merged["client_id"] == "from_file"
    assert merged["use_proto_plus"] is True


def test_cli_overrides_win_over_everything(tmp_path, monkeypatch):
    config_file = tmp_path / "google-ads.yaml"
    config_file.write_text(
        "developer_token: from_file\n"
        "client_id: from_file\n"
        "client_secret: from_file\n"
        "refresh_token: from_file\n"
    )
    monkeypatch.setenv("GOOGLE_ADS_DEVELOPER_TOKEN", "from_env")

    merged = config.load_merged_config(
        config_path=str(config_file),
        cli_overrides={"developer_token": "from_cli"},
    )

    assert merged["developer_token"] == "from_cli"


def _clear_all_auth_env_vars(monkeypatch):
    for env_var in (
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_REFRESH_TOKEN",
        "GOOGLE_ADS_JSON_KEY_FILE_PATH",
        "GOOGLE_ADS_IMPERSONATED_EMAIL",
        "GOOGLE_ADS_USE_APPLICATION_DEFAULT_CREDENTIALS",
    ):
        monkeypatch.delenv(env_var, raising=False)


def test_missing_required_fields_raises(monkeypatch):
    _clear_all_auth_env_vars(monkeypatch)

    with pytest.raises(config.ConfigError):
        config.load_merged_config(config_path="/nonexistent/path/google-ads.yaml")


def test_developer_token_is_optional_with_service_account(monkeypatch):
    _clear_all_auth_env_vars(monkeypatch)

    merged = config.load_merged_config(
        config_path="/nonexistent/path/google-ads.yaml",
        cli_overrides={"json_key_file_path": "/path/to/key.json"},
    )

    assert merged["json_key_file_path"] == "/path/to/key.json"
    assert "developer_token" not in merged


def test_application_default_credentials_env_var_parsed_as_bool(monkeypatch):
    _clear_all_auth_env_vars(monkeypatch)
    monkeypatch.setenv("GOOGLE_ADS_USE_APPLICATION_DEFAULT_CREDENTIALS", "true")

    merged = config.load_merged_config(config_path="/nonexistent/path/google-ads.yaml")

    assert merged["use_application_default_credentials"] is True


def test_adc_false_string_is_not_truthy(monkeypatch):
    _clear_all_auth_env_vars(monkeypatch)
    monkeypatch.setenv("GOOGLE_ADS_USE_APPLICATION_DEFAULT_CREDENTIALS", "false")

    with pytest.raises(config.ConfigError):
        config.load_merged_config(config_path="/nonexistent/path/google-ads.yaml")


def test_write_config_file_sets_restrictive_permissions(tmp_path):
    target = tmp_path / "sub" / "google-ads.yaml"
    written_path = config.write_config_file(
        {
            "developer_token": "x",
            "client_id": "x",
            "client_secret": "x",
            "refresh_token": "x",
        },
        path=target,
    )

    assert written_path == target
    mode = target.stat().st_mode & 0o777
    assert mode == 0o600

    reloaded = config.load_merged_config(config_path=str(target))
    assert reloaded["developer_token"] == "x"
    assert reloaded["use_proto_plus"] is True
