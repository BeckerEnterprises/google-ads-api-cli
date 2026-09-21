"""`gads call <Service> <Methode>` -- generischer Fallback fuer jede API-Methode.

Deckt alles ab, was kein regulaerer `mutate_*`-Aufruf ist: BatchJobService,
ConversionUploadService, OfflineUserDataJobService, KeywordPlanService,
ReachPlanService, GoogleAdsFieldService, CustomerService, Long-Running-
Operations, etc.
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
        service: str = typer.Argument(..., help="Service-Name, z.B. 'BatchJobService'"),
        method: str = typer.Argument(..., help="Methodenname (snake_case), z.B. 'mutate' oder 'run_batch_job'"),
        request_json: str = typer.Option(
            "{}", "--request-json", "-r", help="JSON-Objekt als Request-Payload; mit '@pfad.json' aus Datei laden"
        ),
        no_wait: bool = typer.Option(
            False, "--no-wait", help="Bei Long-Running-Operations nicht auf das Ergebnis warten"
        ),
        timeout: float = typer.Option(
            None, "--timeout", help="Timeout in Sekunden beim Warten auf eine Long-Running-Operation"
        ),
    ) -> None:
        """Ruft eine beliebige Service-Methode generisch auf (voller API-Fallback)."""

        def _run() -> None:
            payload = load_json_arg(request_json)
            if payload is not None and not isinstance(payload, dict):
                raise ValueError("--request-json muss ein JSON-Objekt sein.")

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
        """Listet alle verfuegbaren Service-Namen der aktiven API-Version."""

        def _run() -> None:
            names = proto_bridge.list_service_names(version=ctx.obj["version"])
            formatting.render(names, fmt=ctx.obj["format"])

        _common.run_guarded(ctx, _run)

    @app.command("list-methods")
    def list_methods_cmd(
        ctx: typer.Context, service: str = typer.Argument(..., help="Service-Name, z.B. 'CampaignService'")
    ) -> None:
        """Listet alle aufrufbaren Methoden eines Service auf."""

        def _run() -> None:
            client = _common.build_client(ctx)
            methods = proto_bridge.list_service_methods(client, service, version=ctx.obj["version"])
            formatting.render(methods, fmt=ctx.obj["format"])

        _common.run_guarded(ctx, _run)
