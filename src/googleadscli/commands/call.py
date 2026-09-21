"""`gads call <Service> <Method>` -- generic fallback for any API method.

Covers everything that isn't a regular `mutate_*` call: BatchJobService,
ConversionUploadService, OfflineUserDataJobService, KeywordPlanService,
ReachPlanService, GoogleAdsFieldService, CustomerService, long-running
operations, etc.
"""

from __future__ import annotations

import typer

from googleadscli import formatting, proto_bridge
from googleadscli.commands import _common
from googleadscli.utils import load_json_arg


def register(app: typer.Typer) -> None:
    @app.command("call")
    def call_cmd(
        ctx: typer.Context,
        service: str = typer.Argument(..., help="Service name, e.g. 'BatchJobService'"),
        method: str = typer.Argument(..., help="Method name (snake_case), e.g. 'mutate' or 'run_batch_job'"),
        request_json: str = typer.Option(
            "{}", "--request-json", "-r", help="JSON object as the request payload; load from a file with '@path.json'"
        ),
        no_wait: bool = typer.Option(
            False, "--no-wait", help="Don't wait for the result of long-running operations"
        ),
        timeout: float = typer.Option(
            None, "--timeout", help="Timeout in seconds when waiting for a long-running operation"
        ),
    ) -> None:
        """Generically calls any service method (full API fallback)."""

        def _run() -> None:
            payload = load_json_arg(request_json)
            if payload is not None and not isinstance(payload, dict):
                raise ValueError("--request-json must be a JSON object.")

            client = _common.build_client(ctx)
            result = proto_bridge.invoke_call(
                client,
                service,
                method,
                payload,
                wait_for_operation=not no_wait,
                operation_timeout=timeout,
                version=ctx.obj["version"],
            )
            formatting.render(result, fmt=ctx.obj["format"])

        _common.run_guarded(ctx, _run)

    @app.command("list-services")
    def list_services_cmd(ctx: typer.Context) -> None:
        """Lists all available service names of the active API version."""

        def _run() -> None:
            names = proto_bridge.list_service_names(version=ctx.obj["version"])
            formatting.render(names, fmt=ctx.obj["format"])

        _common.run_guarded(ctx, _run)

    @app.command("list-methods")
    def list_methods_cmd(
        ctx: typer.Context, service: str = typer.Argument(..., help="Service name, e.g. 'CampaignService'")
    ) -> None:
        """Lists all callable methods of a service."""

        def _run() -> None:
            client = _common.build_client(ctx)
            methods = proto_bridge.list_service_methods(client, service, version=ctx.obj["version"])
            formatting.render(methods, fmt=ctx.obj["format"])

        _common.run_guarded(ctx, _run)
