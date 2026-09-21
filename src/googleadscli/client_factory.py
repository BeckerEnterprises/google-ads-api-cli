"""Builds the GoogleAdsClient from the merged configuration."""

from __future__ import annotations

from typing import Any

from google.ads.googleads.client import GoogleAdsClient

from googleadscli.config import ConfigError, load_merged_config

DEFAULT_API_VERSION = "v25"


def build_client(
    *,
    config_path: str | None = None,
    cli_overrides: dict[str, Any] | None = None,
    version: str = DEFAULT_API_VERSION,
) -> GoogleAdsClient:
    merged = load_merged_config(config_path=config_path, cli_overrides=cli_overrides)
    try:
        return GoogleAdsClient.load_from_dict(merged, version=version)
    except Exception as exc:  # configuration error from the client library itself
        raise ConfigError(f"Could not initialize the Google Ads client: {exc}") from exc
