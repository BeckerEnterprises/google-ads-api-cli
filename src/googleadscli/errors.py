"""Structured error handling for agents: JSON on stderr, clear exit codes."""

from __future__ import annotations

import json
import sys
from typing import NoReturn

from google.ads.googleads.errors import GoogleAdsException

from googleadscli.config import ConfigError
from googleadscli.proto_bridge import BridgeError

EXIT_OK = 0
EXIT_CLI_ERROR = 1
EXIT_API_ERROR = 2
EXIT_INTERNAL_ERROR = 70


def format_google_ads_exception(ex: GoogleAdsException) -> dict:
    errors = []
    if ex.failure is not None:
        failure_dict = type(ex.failure).to_dict(
            ex.failure,
            use_integers_for_enums=False,
            preserving_proto_field_name=True,
            always_print_fields_with_no_presence=False,
        )
        for err in failure_dict.get("errors", []):
            error_code = err.get("error_code", {}) or {}
            code_type = next(iter(error_code), None)
            field_path = None
            elements = err.get("location", {}).get("field_path_elements", [])
            if elements:
                parts = []
                for el in elements:
                    part = el.get("field_name", "")
                    if "index" in el:
                        part += f"[{el['index']}]"
                    parts.append(part)
                field_path = ".".join(parts)
            errors.append(
                {
                    "error_code_type": code_type,
                    "error_code": error_code.get(code_type) if code_type else None,
                    "message": err.get("message"),
                    "field_path": field_path,
                    "trigger": err.get("trigger"),
                }
            )

    status_code = None
    if getattr(ex, "call", None) is not None and hasattr(ex.call, "code"):
        code = ex.call.code()
        status_code = getattr(code, "name", str(code))

    return {
        "type": "GoogleAdsException",
        "request_id": ex.request_id,
        "status_code": status_code,
        "errors": errors,
    }


def emit_error(payload: dict, *, exit_code: int) -> NoReturn:
    print(json.dumps(payload, indent=2, ensure_ascii=False), file=sys.stderr)
    raise SystemExit(exit_code)


def handle_exception(exc: Exception, *, debug: bool = False) -> NoReturn:
    if isinstance(exc, GoogleAdsException):
        emit_error(format_google_ads_exception(exc), exit_code=EXIT_API_ERROR)
    if isinstance(exc, (ConfigError, BridgeError, ValueError)):
        emit_error({"type": type(exc).__name__, "message": str(exc)}, exit_code=EXIT_CLI_ERROR)

    if debug:
        raise exc
    emit_error(
        {"type": "InternalError", "message": str(exc)},
        exit_code=EXIT_INTERNAL_ERROR,
    )
