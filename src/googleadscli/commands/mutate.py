"""`gads mutate <resource>` -- generischer Create/Update/Remove fuer jede Ressource."""

from __future__ import annotations

import typer

from googleadscli import formatting, proto_bridge
from googleadscli.commands import _common
from googleadscli.utils import load_json_arg, normalize_customer_id


def register(app: typer.Typer) -> None:
    @app.command("mutate")
    def mutate_cmd(
        ctx: typer.Context,
        resource: str = typer.Argument(
            ..., help="Ressourcen-Key in snake_case, z.B. 'campaign', 'ad_group_criterion'"
        ),
        customer_id: str = typer.Option(..., "--customer-id", "-c"),
        operations_json: str = typer.Option(
            ...,
            "--operations-json",
            "-o",
            help="JSON-Array von Operationen ({'create'|'update'|'remove': ...}); "
            "mit '@pfad.json' aus Datei laden",
        ),
        dry_run: bool = typer.Option(
            False, "--dry-run", help="validate_only: nur validieren, nichts aendern"
        ),
        partial_failure: bool = typer.Option(
            False, "--partial-failure", help="Einzelne fehlschlagende Operationen nicht die ganze Anfrage abbrechen lassen"
        ),
    ) -> None:
        """Fuehrt create/update/remove-Operationen fuer eine Ressource aus."""

        def _run() -> None:
            operations = load_json_arg(operations_json)
            if not isinstance(operations, list):
                raise ValueError("--operations-json muss ein JSON-Array von Operationen sein.")

            client = _common.build_client(ctx)
            result = proto_bridge.run_mutate(
                client,
                resource,
                normalize_customer_id(customer_id),
                operations,
                partial_failure=partial_failure,
                validate_only=dry_run,
                version=ctx.obj["version"],
            )
            formatting.render(result, fmt=ctx.obj["format"])

        _common.run_guarded(ctx, _run)
