"""UI layout tiggering and showing the process of the simulation."""

import datetime
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, ctx, dcc, html

import utils.constants as consts
from utils import file_utils, rule_utils
from utils.logger import logger

from . import model_rule_sim

dash.register_page(
    __name__,
    path=consts.PAGE_SIM_PROCESS_URL,
    title=consts.PAGE_SIM_PROCESS_TITLE_NAME,
    name=consts.PAGE_SIM_PROCESS_TITLE_NAME,
)

page_heading = html.Div(
    [
        html.H2("Simulation starten", id="heading-simulator-process"),
        html.P(
            "Namen für Statistik Export eingeben:",
            id="subheading-simulator-process",
        ),
        html.Hr(),
    ],
)

stat_naming = html.Div(
    [
        html.H3("Name für Statistik:", className="mb-3"),
        dbc.Row(
            [
                # Rule naming
                dbc.Col(
                    dbc.Input(
                        id="input-simulator-stat-name",
                        size="sm",
                    ),
                    width=4,
                ),
                dbc.Tooltip(
                    "Gibt den Name für den Ordner an, in dem die"
                    " Statistikdateien der Simulation gespeichert werden.",
                    target="input-simulator-stat-name",
                    placement="top",
                ),
            ],
            className="mb-3",
        ),
        html.Hr(),
    ],
)

start_simulation = html.Div(
    [
        dbc.Button(
            [
                dbc.Spinner(
                    html.Div(id="spinner-simulator-start"),
                ),
                "Simulation starten",
            ],
            color="primary",
            id="button-simulator-start",
            size="lg",
        ),
    ],
    className="mb-3",
)


import_log = html.Div(
    [
        dcc.Interval(
            id="interval-simulator",
            interval=500,
            n_intervals=0,
        ),
        dcc.Textarea(
            id="log-simulator",
            style={"width": "100%", "height": "42vh"},
            disabled=True,
        ),
        html.Hr(className="mt-5"),
    ],
)

page_navigation = html.Div(
    [
        dbc.Stack(
            [
                dbc.Button(
                    "Zurück",
                    href=consts.PAGE_SIM_START_URL,
                    outline=True,
                    color="primary",
                    className="me-auto",
                    id="button-simulator-process-back",
                ),
                dbc.Button(
                    id="button-simulator-process-next",
                    className="ms-auto",
                    color="primary",
                    disabled=True,
                    href=consts.PAGE_DB_MANAGER_URL,
                ),
            ],
            direction="horizontal",
            gap=3,
            className="mb-5",
        ),
    ],
)


import_db_file = html.Div(
    [
        dcc.Location(id="url-simulator-process"),
        page_heading,
        stat_naming,
        start_simulation,
        import_log,
        page_navigation,
    ],
    className="page-container",
)

layout = dbc.Container(import_db_file, fluid=False, className="main-container")


@callback(
    Output("input-simulator-stat-name", "value"),
    Input("url-simulator-process", "search"),
    Input("url-simulator-process", "pathname"),
)
def get_standard_name_from_url(search, pathname):
    """Load db and ruleset name from query string."""
    if search and pathname == consts.PAGE_SIM_PROCESS_URL:
        filename_db = file_utils.get_query_string(search, "filename")
        filename_db = Path(filename_db).stem
        ruleset = file_utils.get_query_string(search, "ruleset")
        ruleset = Path(ruleset).stem

        return f"{filename_db} - {ruleset} - {datetime.datetime.now().strftime('%Y-%m-%d %H-%M')}"

    return None


@callback(
    [
        Output("button-simulator-process-next", "disabled"),
        Output("button-simulator-process-next", "children"),
        Output("interval-simulator", "disabled"),
        Output("heading-simulator-process", "children"),
        Output("subheading-simulator-process", "children"),
        Output("spinner-simulator-start", "children"),
    ],
    Input("button-simulator-start", "n_clicks"),
    Input("url-simulator-process", "search"),
    Input("input-simulator-stat-name", "value"),
)
def run_simulation(n_clicks, search, value_stat_name):
    """Start simulator algorithm."""
    if (
        n_clicks
        and search
        and value_stat_name
        and ctx.triggered_id == "button-simulator-start"
    ):
        database_name = file_utils.get_query_string(search, "filename")
        ruleset_name = file_utils.get_query_string(search, "ruleset")

        rule_preselection, list_rule_assignments = rule_utils.read_rule_file(
            consts.FOLDER_RULE_FILES,
            ruleset_name,
        )
        value_stat_name = file_utils.remove_invalid_input_field_characters(
            value_stat_name,
        )

        # Outputs false if rule sim fails
        if model_rule_sim.rule_simulator(
            rule_preselection,
            list_rule_assignments,
            database_name,
            ruleset_name,
            value_stat_name,
        ):
            return (
                False,
                [
                    html.I(className="bi bi-check-circle-fill me-2"),
                    "Weiter",
                ],
                True,
                "Simulation fertiggestellt!",
                "Weiter für die Ergebnisanzeige.",
                "",
            )
        else:
            return (
                False,
                [
                    html.I(className="bi bi-x-octagon-fill me-2"),
                    "Zum DB Manager",
                ],
                True,
                "Simulation fehlgeschlagen",
                "Seite kann verlassen werden.",
                "",
            )

    return (
        True,
        "Weiter",
        False,
        "Simulation starten",
        "Namen für Statistik Export eingeben:",
        "",
    )


@callback(
    Output("button-simulator-start", "disabled"),
    Input("button-simulator-start", "n_clicks"),
)
def hide_start_button_when_clicked(n_clicks):
    """Hide start button on click."""
    if n_clicks:
        return True

    return False


@callback(
    Output("log-simulator", "disabled"),
    Input("url-simulator-process", "pathname"),
)
def clear_log(pathname):
    """Clear the log on pageload."""
    logger.log_stream.truncate(0)
    logger.log_stream.seek(0)

    return True


@callback(
    Output("log-simulator", "value"),
    Input("interval-simulator", "n_intervals"),
)
def update_log(_):
    """Update the browser textarea with log data in intervals."""
    content = logger.log_stream.getvalue()
    content = content.replace(consts.CONSOLE_GREEN, "")
    content = content.replace(consts.CONSOLE_BLUE, "")
    content = content.replace(consts.CONSOLE_RED, "")
    content = content.replace(consts.CONSOLE_YELLOW, "")
    content = content.replace(consts.CONSOLE_ENDCMD, "")

    return content


@callback(
    Output("button-simulator-process-back", "href"),
    Input("url-simulator-process", "search"),
)
def update_href_back_button(search):
    """Set back button href to current query string."""
    return f"{consts.PAGE_SIM_RULE_EDITOR_URL}{search}"


@callback(
    Output("button-simulator-process-next", "href"),
    Input("url-simulator-process", "search"),
    Input("url-simulator-process", "pathname"),
    Input("input-simulator-stat-name", "value"),
)
def update_href_next_button(search, pathname, value_stat_name):
    """Add stat name to next button href for end overview page."""
    if search and pathname == consts.PAGE_SIM_PROCESS_URL:
        value_stat_name = file_utils.remove_invalid_input_field_characters(
            value_stat_name,
        )
        search = f"{search}&stat_a={value_stat_name}"

        return f"{consts.PAGE_SIM_DONE_URL}{search}"


@callback(
    Output("url-simulator-process", "href"),
    Input("url-simulator-process", "search"),
    Input("url-simulator-process", "pathname"),
)
def redirect_when_missing_query_string(search, pathname):
    """Redirect to home page if query string is missing."""
    if (
        not search
        and not file_utils.get_query_string(search, "filename")
        and not file_utils.get_query_string(search, "ruleset")
        and pathname != consts.PAGE_SIM_PROCESS_URL
        and pathname != consts.PAGE_SIM_DONE_URL
    ):
        logger.error(
            "Keine Datenbank oder Regelset Angabe im Query String gefunden!"
            " Bitte dem Programmablauf folgen und ab dem Datenbank Manager"
            " starten.",
        )
        return consts.PAGE_HOME_URL
