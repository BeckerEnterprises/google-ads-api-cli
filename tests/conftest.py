"""Shared test fixtures.

Constructing a GoogleAdsClient (even just for reflection over service/message
classes) normally triggers a real OAuth refresh call (see
google.ads.googleads.oauth2). Since reflection and JSON<->proto conversion
themselves work fully offline, the credentials refresh is simply patched to a
no-op here -- all further tests run without network access, against real
generated protobuf/GAPIC classes.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def fake_client():
    from unittest.mock import patch

    from google.oauth2.credentials import Credentials

    with patch.object(Credentials, "refresh", lambda self, request: None):
        from google.ads.googleads.client import GoogleAdsClient

        yield GoogleAdsClient.load_from_dict(
            {
                "developer_token": "fake_dev_token",
                "client_id": "fake_client_id",
                "client_secret": "fake_client_secret",
                "refresh_token": "fake_refresh_token",
                "use_proto_plus": True,
            },
            version="v25",
        )
