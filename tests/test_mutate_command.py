"""End-to-end test of the `gads mutate` command via the Typer CLI."""

from __future__ import annotations

import json
from unittest.mock import patch

from typer.testing import CliRunner

from googleadscli.cli import app

runner = CliRunner()


def test_mutate_command_create_campaign(fake_client):
    from google.ads.googleads.v25.services.services.campaign_service.client import (
        CampaignServiceClient,
    )
    from google.ads.googleads.v25.services.types.campaign_service import (
        MutateCampaignResult,
        MutateCampaignsResponse,
    )

    fake_response = MutateCampaignsResponse(
        results=[MutateCampaignResult(resource_name="customers/123/campaigns/999")]
    )
    operations = json.dumps(
        [{"create": {"name": "Test Campaign", "status": "PAUSED", "advertising_channel_type": "SEARCH"}}]
    )

    with patch("googleadscli.commands._common.build_client", return_value=fake_client), patch.object(
        CampaignServiceClient, "mutate_campaigns", autospec=True, return_value=fake_response
    ) as mocked:
        result = runner.invoke(
            app,
            [
                "mutate",
                "campaign",
                "--customer-id",
                "123",
                "--operations-json",
                operations,
            ],
        )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload == {"results": [{"resource_name": "customers/123/campaigns/999"}]}
    sent_request = mocked.call_args.kwargs["request"]
    assert sent_request.customer_id == "123"
    assert sent_request.validate_only is False


def test_mutate_command_dry_run_sets_validate_only(fake_client):
    from google.ads.googleads.v25.services.services.campaign_service.client import (
        CampaignServiceClient,
    )
    from google.ads.googleads.v25.services.types.campaign_service import MutateCampaignsResponse

    operations = json.dumps([{"remove": "customers/123/campaigns/999"}])

    with patch("googleadscli.commands._common.build_client", return_value=fake_client), patch.object(
        CampaignServiceClient, "mutate_campaigns", autospec=True, return_value=MutateCampaignsResponse()
    ) as mocked:
        result = runner.invoke(
            app,
            [
                "mutate",
                "campaign",
                "--customer-id",
                "123",
                "--operations-json",
                operations,
                "--dry-run",
            ],
        )

    assert result.exit_code == 0, result.output
    assert mocked.call_args.kwargs["request"].validate_only is True


def test_mutate_command_invalid_operations_json_exits_1():
    result = runner.invoke(
        app,
        ["mutate", "campaign", "--customer-id", "123", "--operations-json", '{"not": "a list"}'],
    )
    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert "must be a JSON array" in payload["message"]
