"""UI layout to show basic information about the simulation results."""

import warnings

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, callback, dcc, html

import utils.constants as consts
from utils import file_utils, layout_utils, rule_utils
from utils.logger import logger

# Ignore FutureWarning from Pandas, triggered by internal Plotly Express Code
# which I have no control over
warnings.filterwarnings("ignore", category=FutureWarning)

dash.register_page(
    __name__,
    path=consts.PAGE_SIM_DONE_URL,
    title=consts.PAGE_SIM_DONE_TITLE_NAME,
    name=consts.PAGE_SIM_DONE_TITLE_NAME,
)

page_heading = html.Div(
    [
        html.H2("Simulations-Ergebnis"),
        html.P(
            "Ergebnis-Übersicht der Simulation."
        ),
    ],
)


page_navigation = html.Div(
    [
        dbc.Stack(
            [
                dbc.Button(
                    "Weiter zur Startseite",
                    href=consts.PAGE_HOME_URL,
                    color="primary",
                    className="ms-auto",
                    id="button-end-overview-next",
                ),
            ],
            direction="horizontal",
            className="mb-5",
        ),
    ],
)

data_overview = html.Div(
    [
        dbc.Spinner(
            children=html.Div(id="spinner-end-overview"),
            size="md",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.P(id="text-end-overview-count-accepted"),
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        html.P(id="text-end-overview-count-denied"),
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        html.P(id="text-end-overview-count-combo"),
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        html.P(id="text-end-overview-count-enrolled"),
                    ],
                    width=3,
                ),
            ],
        ),
    ],
)


barchart = html.Div(
    id="barchart-end-overview",
)

piechart = html.Div(id="piechart-end-overview")


sim_end_overview = html.Div(
    [
        dcc.Location(id="url-end-overview"),
        page_heading,
        html.Hr(),
        data_overview,
        barchart,
        piechart,
        html.Hr(),
        page_navigation,
    ],
    className="page-container",
)


layout = html.Div(
    [
        dbc.Container(
            sim_end_overview,
            fluid=False,
            className="main-container",
        ),
    ],
)


@callback(
    Output("spinner-end-overview", "children"),
    Output("text-end-overview-count-accepted", "children"),
    Output("text-end-overview-count-denied", "children"),
    Output("text-end-overview-count-combo", "children"),
    Output("text-end-overview-count-enrolled", "children"),
    Output("barchart-end-overview", "children"),
    Output("piechart-end-overview", "children"),
    Output("barchart-end-overview", "style"),
    Output("piechart-end-overview", "style"),
    Input("url-end-overview", "search"),
    Input("url-end-overview", "pathname"),
)
def show_db_assignment_info(search, pathname):
    if search and pathname == consts.PAGE_SIM_DONE_URL:
        stat_name = file_utils.get_query_string(search, "stat_a")
        (
            stat_info,
            df_accepted_assignments,
            df_denied_assignments,
            df_accepted_lecture_combinations,
            df_assignments,
        ) = rule_utils.read_stat_files(stat_name)

        df_new_assignments = pd.concat(
            [
                df_accepted_assignments,
                df_denied_assignments,
                df_accepted_lecture_combinations,
            ],
        )

        if not df_new_assignments.empty:
            barchart = html.Div(
                [
                    html.H5(
                        "Anzahl Belegungen pro Regel und neuem Status",
                        className=("mt-5"),
                    ),
                    dcc.Graph(
                        figure=layout_utils.create_barchart_for_rules(
                            df_new_assignments,
                            stat_info,
                        ),
                    ),
                ],
            )

            piechart = html.Div(
                [
                    html.H5("Aufteilung der neuen Status", className=("mt-5")),
                    dcc.Graph(
                        figure=layout_utils.create_piechart_for_assignment_status(
                            df_new_assignments,
                        ),
                    ),
                ],
            )

            return (
                "",
                f"Anzahl neue Zulassungen: {len(df_accepted_assignments)}",
                f"Anzahl neue Ablehnungen: {len(df_denied_assignments)}",
                "Anzahl neue Kombinationszulassungen:"
                f" {len(df_accepted_lecture_combinations)}",
                "Anzahl ausstehende Anmeldungen:"
                f" {len(df_assignments[df_assignments["status"] == consts.RULE_SETTING_STATUS_ENROLLED])}",
                barchart,
                piechart,
                {},
                {},
            )

        else:
            return (
                "",
                "Anzahl neue Zulassungen: 0",
                "Anzahl neue Ablehnungen: 0",
                "Anzahl neue Kombinationszulassungen: 0",
                "Anzahl ausstehende Anmeldungen: 0",
                None,
                None,
                {"visibility": "hidden"},
                {"visibility": "hidden"},
            )

    return (
        "",
        "",
        "",
        "",
        "",
        None,
        None,
        {"visibility": "hidden"},
        {"visibility": "hidden"},
    )


@callback(
    Output("url-end-overview", "href"),
    Input("url-end-overview", "search"),
    Input("url-end-overview", "pathname"),
)
def redirect_when_missing_query_string(search, pathname):
    """Redirect to home page if query string is missing."""
    if (
        not search
        and not file_utils.get_query_string(search, "stat_a")
        and pathname != consts.PAGE_SIM_DONE_URL
        and pathname != consts.PAGE_HOME_URL
    ):
        logger.error(
            "Keine Statistik Angabe im Query String gefunden! Bitte dem"
            " Programmablauf folgen und ab dem Datenbank Manager starten.",
        )
        return consts.PAGE_HOME_URL
