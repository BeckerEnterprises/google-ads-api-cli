"""Tests fuer die strukturierte Fehlerausgabe (GoogleAdsException -> JSON)."""

from __future__ import annotations

import json

import grpc
import pytest

from googleadscli import errors


class _FakeGrpcCall:
    def code(self):
        return grpc.StatusCode.INVALID_ARGUMENT


def _build_synthetic_exception():
    from google.ads.googleads.errors import GoogleAdsException
    from google.ads.googleads.v25.errors.types.errors import GoogleAdsError, GoogleAdsFailure
    from google.ads.googleads.v25.errors.types.request_error import RequestErrorEnum

    error = GoogleAdsError(
        message="Campaign budget not found.",
        error_code={"request_error": RequestErrorEnum.RequestError.RESOURCE_NOT_FOUND},
        location={
            "field_path_elements": [
                {"field_name": "operations"},
                {"field_name": "create", "index": 0},
            ]
        },
    )
    failure = GoogleAdsFailure(errors=[error])
    return GoogleAdsException(
        error=grpc.RpcError(),
        call=_FakeGrpcCall(),
        failure=failure,
        request_id="req-123",
    )


def test_format_google_ads_exception_structure():
    exc = _build_synthetic_exception()
    payload = errors.format_google_ads_exception(exc)

    assert payload["type"] == "GoogleAdsException"
    assert payload["request_id"] == "req-123"
    assert payload["status_code"] == "INVALID_ARGUMENT"
    assert len(payload["errors"]) == 1
    err = payload["errors"][0]
    assert err["error_code_type"] == "request_error"
    assert err["error_code"] == "RESOURCE_NOT_FOUND"
    assert err["message"] == "Campaign budget not found."
    assert err["field_path"] == "operations.create[0]"


def test_handle_exception_google_ads_exception_exits_2(capsys):
    exc = _build_synthetic_exception()
    with pytest.raises(SystemExit) as exc_info:
        errors.handle_exception(exc)
    assert exc_info.value.code == errors.EXIT_API_ERROR

    stderr_payload = json.loads(capsys.readouterr().err)
    assert stderr_payload["type"] == "GoogleAdsException"


def test_handle_exception_value_error_exits_1(capsys):
    with pytest.raises(SystemExit) as exc_info:
        errors.handle_exception(ValueError("bad input"))
    assert exc_info.value.code == errors.EXIT_CLI_ERROR

    stderr_payload = json.loads(capsys.readouterr().err)
    assert stderr_payload["message"] == "bad input"


def test_handle_exception_unexpected_error_exits_70(capsys):
    with pytest.raises(SystemExit) as exc_info:
        errors.handle_exception(RuntimeError("boom"))
    assert exc_info.value.code == errors.EXIT_INTERNAL_ERROR


def test_handle_exception_debug_reraises():
    with pytest.raises(RuntimeError):
        errors.handle_exception(RuntimeError("boom"), debug=True)
