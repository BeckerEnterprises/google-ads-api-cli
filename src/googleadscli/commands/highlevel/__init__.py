"""Komfortbefehle fuer haeufige Workflows -- duenne Wrapper ueber `mutate`/`call`.

Vollstaendigkeit ist bereits durch die generischen Basisbefehle (query/mutate/
call) gegeben; diese Befehle dienen nur der Ergonomie.
"""

from __future__ import annotations

import typer

from googleadscli.commands.highlevel import ad, ad_group, budget, campaign, keyword

app = typer.Typer(no_args_is_help=True, help="Komfortbefehle fuer haeufige Workflows")
app.add_typer(budget.app, name="budget")
app.add_typer(campaign.app, name="campaign")
app.add_typer(ad_group.app, name="ad-group")
app.add_typer(keyword.app, name="keyword")
app.add_typer(ad.app, name="ad")
