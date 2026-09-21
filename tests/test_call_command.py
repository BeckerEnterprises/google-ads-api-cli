"""End-to-end test of the generic `gads call` command via the Typer CLI."""

from __future__ import annotations

import json
from unittest.mock import patch

from typer.testing import CliRunner

from googleadscli.cli import app

runner = CliRunner()


def test_call_command_invokes_arbitrary_service_method(fake_client):
    from google.ads.googleads.v25.resources.types.google_ads_field import GoogleAdsField
    from google.ads.googleads.v25.services.services.google_ads_field_service.client import (
        GoogleAdsFieldServiceClient,
    )

    fake_field = GoogleAdsField(name="campaign.id", category="ATTRIBUTE", data_type="INT64", selectable=True)

    with patch("googleadscli.commands._common.build_client", return_value=fake_client), patch.object(
        GoogleAdsFieldServiceClient, "get_google_ads_field", autospec=True, return_value=fake_field
    ):
        result = runner.invoke(
            app,
            [
                "call",
                "GoogleAdsFieldService",
                "get_google_ads_field",
                "--request-json",
                json.dumps({"resource_name": "googleAdsFields/campaign.id"}),
            ],
        )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["name"] == "campaign.id"


def test_call_command_unknown_service_exits_1(fake_client):
    with patch("googleadscli.commands._common.build_client", return_value=fake_client):
        result = runner.invoke(app, ["call", "NotAService", "whatever"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["type"] == "BridgeError"


def test_list_services_command_works_without_credentials():
    result = runner.invoke(app, ["list-services"])
    assert result.exit_code == 0, result.output
    names = json.loads(result.output)
    assert "CampaignService" in names
