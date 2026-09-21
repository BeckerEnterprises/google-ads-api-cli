"""Config precedence: CLI flags > GOOGLE_ADS_* env vars > config file."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "google-ads-cli" / "google-ads.yaml"
LEGACY_CONFIG_PATH = Path.home() / "google-ads.yaml"

# Field name (google-ads.yaml / GoogleAdsClient) -> env var name
ENV_VAR_MAP = {
    "developer_token": "GOOGLE_ADS_DEVELOPER_TOKEN",
    # OAuth2 installed-app flow (interactive consent, see 'gads auth login').
    "client_id": "GOOGLE_ADS_CLIENT_ID",
    "client_secret": "GOOGLE_ADS_CLIENT_SECRET",
    "refresh_token": "GOOGLE_ADS_REFRESH_TOKEN",
    # OAuth2 service-account flow: JSON key file from the Google Cloud
    # Console, whose client_email is added directly as a user on the Google
    # Ads account (or MCC) -- no interactive consent needed.
    "json_key_file_path": "GOOGLE_ADS_JSON_KEY_FILE_PATH",
    # Only needed for domain-wide delegation (service account impersonates a
    # real Workspace user). Left empty when the service account has been
    # granted direct access to the Ads account.
    "impersonated_email": "GOOGLE_ADS_IMPERSONATED_EMAIL",
    # Application Default Credentials (e.g. GOOGLE_APPLICATION_CREDENTIALS
    # or 'gcloud auth application-default login').
    "use_application_default_credentials": "GOOGLE_ADS_USE_APPLICATION_DEFAULT_CREDENTIALS",
    "login_customer_id": "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
    "linked_customer_id": "GOOGLE_ADS_LINKED_CUSTOMER_ID",
}

CONFIG_PATH_ENV_VAR = "GOOGLE_ADS_CONFIGURATION_FILE_PATH"

_TRUTHY = {"true", "1", "yes"}


class ConfigError(Exception):
    """Invalid or missing Google Ads configuration."""


def _resolve_config_path(explicit_path: str | None) -> Path | None:
    if explicit_path:
        return Path(explicit_path).expanduser()
    env_path = os.environ.get(CONFIG_PATH_ENV_VAR)
    if env_path:
        return Path(env_path).expanduser()
    if DEFAULT_CONFIG_PATH.exists():
        return DEFAULT_CONFIG_PATH
    if LEGACY_CONFIG_PATH.exists():
        return LEGACY_CONFIG_PATH
    return None


def _load_config_file(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"Invalid format in config file: {path}")
    return data


def load_merged_config(
    *,
    config_path: str | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Builds the final config dict for GoogleAdsClient.load_from_dict.

    Precedence (low -> high): config file < env vars < CLI flags.
    """
    merged: dict[str, Any] = _load_config_file(_resolve_config_path(config_path))

    for field, env_var in ENV_VAR_MAP.items():
        value = os.environ.get(env_var)
        if value:
            merged[field] = value

    if cli_overrides:
        merged.update({k: v for k, v in cli_overrides.items() if v is not None})

    if isinstance(merged.get("use_application_default_credentials"), str):
        merged["use_application_default_credentials"] = (
            merged["use_application_default_credentials"].strip().lower() in _TRUTHY
        )

    # Enforces the bridge invariant: proto-plus wrappers (not raw protobuf
    # messages). proto-plus's own .to_dict()/.from_json() and dict
    # constructors give a much simpler generic JSON<->message conversion than
    # raw pb2 messages, and the GAPIC method signatures are annotated against
    # proto-plus types anyway.
    merged["use_proto_plus"] = True

    has_installed_app = all(merged.get(f) for f in ("client_id", "client_secret", "refresh_token"))
    has_service_account = bool(merged.get("json_key_file_path"))
    has_adc = bool(merged.get("use_application_default_credentials"))

    if not (has_installed_app or has_service_account or has_adc):
        raise ConfigError(
            "No Google Ads credentials found. One of the following methods is required: "
            "(1) OAuth installed-app flow (client_id, client_secret, refresh_token -- set up via "
            "'gads auth login'), (2) a service-account JSON key file "
            "(json_key_file_path, e.g. via --json-key-file-path/GOOGLE_ADS_JSON_KEY_FILE_PATH; "
            "the key file's client_email must be added as a user on the Google Ads account), "
            "or (3) Application Default Credentials "
            "(use_application_default_credentials=true). "
            f"Alternatively, create a config file at {DEFAULT_CONFIG_PATH}. "
            "'developer_token' is optional (not needed under cloud-managed access without a "
            "classic developer token)."
        )

    return merged


def write_config_file(data: dict[str, Any], path: Path | None = None) -> Path:
    """Writes the config file with restrictive file permissions (0600)."""
    target = path or DEFAULT_CONFIG_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    to_write = dict(data)
    to_write.setdefault("use_proto_plus", True)
    with target.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(to_write, fh, default_flow_style=False)
    target.chmod(0o600)
    return target
