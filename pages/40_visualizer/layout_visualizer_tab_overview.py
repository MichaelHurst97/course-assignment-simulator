"""Div with basic stat info for the current db both rulesets use."""

from pathlib import Path

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, html

from .layout_visualizer_data_store import data_store

tab_overview = html.Div(id="div-visualizer-overview")


@callback(
    Output("div-visualizer-overview", "children"),
    Input("data-store-loaded-check", "hidden"),
)
def create_stat_overview(data_store_loaded):
    """Create a stat overview consinsting of simple text info
    regarding both rulesets.

    """
    if data_store_loaded:
        # Data in here is common between both datasets.
        # Use a, because a is always present.
        # Both datasets can differ
        stat_info = data_store["stat_info_a"]

        database_name = Path(stat_info["database_filename"]).stem
        database_id = stat_info["database_id"]
        semester = stat_info["assignment_semester"]

        data_overview = [
            html.Hr(),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.P(f"Datenbankname: {database_name}"),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            html.P(f"Datenbank-ID: {database_id}"),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            html.P(f"Semester: {semester}"),
                        ],
                        width=4,
                    ),
                ],
            ),
        ]

        return html.Div(data_overview)
    return None
