"""Konfigurations-Precedence: CLI-Flags > GOOGLE_ADS_*-Env-Vars > Config-Datei."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "google-ads-cli" / "google-ads.yaml"
LEGACY_CONFIG_PATH = Path.home() / "google-ads.yaml"

# Feldname (google-ads.yaml / GoogleAdsClient) -> Env-Var-Name
ENV_VAR_MAP = {
    "developer_token": "GOOGLE_ADS_DEVELOPER_TOKEN",
    # OAuth2 Installed-App-Flow (interaktiver Consent, siehe 'gads auth login').
    "client_id": "GOOGLE_ADS_CLIENT_ID",
    "client_secret": "GOOGLE_ADS_CLIENT_SECRET",
    "refresh_token": "GOOGLE_ADS_REFRESH_TOKEN",
    # OAuth2 Service-Account-Flow: JSON-Schluesseldatei aus der Google Cloud
    # Console, deren client_email direkt als Nutzer auf dem Google-Ads-Konto
    # (oder MCC) hinterlegt wird -- kein interaktiver Consent noetig.
    "json_key_file_path": "GOOGLE_ADS_JSON_KEY_FILE_PATH",
    # Nur fuer Domain-Wide-Delegation noetig (Service Account impersoniert
    # einen echten Workspace-Nutzer). Bei direkt freigeschaltetem Service-
    # Account-Zugriff auf das Ads-Konto bleibt dies leer.
    "impersonated_email": "GOOGLE_ADS_IMPERSONATED_EMAIL",
    # Application Default Credentials (z.B. GOOGLE_APPLICATION_CREDENTIALS
    # oder 'gcloud auth application-default login').
    "use_application_default_credentials": "GOOGLE_ADS_USE_APPLICATION_DEFAULT_CREDENTIALS",
    "login_customer_id": "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
    "linked_customer_id": "GOOGLE_ADS_LINKED_CUSTOMER_ID",
}

CONFIG_PATH_ENV_VAR = "GOOGLE_ADS_CONFIGURATION_FILE_PATH"

_TRUTHY = {"true", "1", "yes"}


class ConfigError(Exception):
    """Fehlerhafte oder fehlende Google-Ads-Konfiguration."""


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
        raise ConfigError(f"Ungueltiges Format in Config-Datei: {path}")
    return data


def load_merged_config(
    *,
    config_path: str | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Baut das finale Config-Dict fuer GoogleAdsClient.load_from_dict.

    Precedence (niedrig -> hoch): Config-Datei < Env-Vars < CLI-Flags.
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

    # Erzwingt die Bridge-Invariante: proto-plus-Wrapper (nicht rohe Protobuf-Messages).
    # proto-plus liefert mit .to_dict()/.from_json() und Dict-Konstruktoren eine deutlich
    # einfachere generische JSON<->Message-Konvertierung als rohe pb2-Messages, und die
    # GAPIC-Methodensignaturen sind ohnehin stets gegen proto-plus-Typen annotiert.
    merged["use_proto_plus"] = True

    has_installed_app = all(merged.get(f) for f in ("client_id", "client_secret", "refresh_token"))
    has_service_account = bool(merged.get("json_key_file_path"))
    has_adc = bool(merged.get("use_application_default_credentials"))

    if not (has_installed_app or has_service_account or has_adc):
        raise ConfigError(
            "Keine Google-Ads-Zugangsdaten gefunden. Eine der folgenden Methoden wird benoetigt: "
            "(1) OAuth Installed-App-Flow (client_id, client_secret, refresh_token -- via "
            "'gads auth login' einrichten), (2) Service-Account-JSON-Schluesseldatei "
            "(json_key_file_path, z.B. per --json-key-file-path/GOOGLE_ADS_JSON_KEY_FILE_PATH; "
            "die client_email der Schluesseldatei muss als Nutzer auf dem Google-Ads-Konto "
            "hinterlegt sein), oder (3) Application Default Credentials "
            "(use_application_default_credentials=true). "
            f"Alternativ eine Config-Datei unter {DEFAULT_CONFIG_PATH} anlegen. "
            "'developer_token' ist optional (nicht noetig bei Cloud-managed Access ohne "
            "klassischen Developer Token)."
        )

    return merged


def write_config_file(data: dict[str, Any], path: Path | None = None) -> Path:
    """Schreibt die Config-Datei mit restriktiven Dateirechten (0600)."""
    target = path or DEFAULT_CONFIG_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    to_write = dict(data)
    to_write.setdefault("use_proto_plus", True)
    with target.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(to_write, fh, default_flow_style=False)
    target.chmod(0o600)
    return target
