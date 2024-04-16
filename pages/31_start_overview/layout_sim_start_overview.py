"""UI layout for inspecting db before rule simulation."""

import sqlite3
from contextlib import closing

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

import utils.constants as consts
from utils import db_utils, file_utils
from utils.logger import logger

dash.register_page(
    __name__,
    path=consts.PAGE_SIM_START_URL,
    title=consts.PAGE_SIM_START_TITLE_NAME,
    name=consts.PAGE_SIM_START_TITLE_NAME,
)


def get_db_data_for_grid(filename):
    """Fetch assignment table rows to show in grid.

    Limited by setting so browser doesn't crash when trying to
    load a very large number of assignments.
    """
    database_path = db_utils.get_db_path(filename, True)
    with closing(sqlite3.connect(database_path)) as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT * FROM {consts.TABLE_NAME_ASSIGNMENTS}"
            f" LIMIT {consts.OVERVIEW_SETTING_MAX_PREVIEW_SIZE}",
        )
        rows = cursor.fetchall()
        columnDefs = [
            {
                "field": column[0],
                "width": 140,
                "suppressMovable": True,
                "resizable": True,
            }
            for column in cursor.description
        ]

        records = [
            dict(
                zip(
                    [column[0] for column in cursor.description],
                    row,
                    strict=False,
                ),
            )
            for row in rows
        ]

        return records, columnDefs


def get_db_assignment_info(filename):
    """Fetch data regarding overall assignment information of db."""
    database_path = db_utils.get_db_path(filename, True)
    with closing(sqlite3.connect(database_path)) as conn:
        table_assignments = consts.TABLE_NAME_ASSIGNMENTS
        table_internal = consts.TABLE_NAME_INTERNAL

        cursor = conn.cursor()

        cursor.execute(
            f"SELECT COUNT(*) FROM {table_assignments}"
            f" WHERE status = '{consts.RULE_SETTING_STATUS_ACCEPTED}'",
        )

        count_accepted = cursor.fetchone()[0]

        cursor.execute(
            f"SELECT COUNT(*) FROM {table_assignments}"
            f" WHERE status = '{consts.RULE_SETTING_STATUS_ENROLLED}'",
        )
        count_enrolled = cursor.fetchone()[0]

        cursor.execute(
            f"SELECT COUNT(*) FROM {table_assignments}"
            f" WHERE status = '{consts.RULE_SETTING_STATUS_DENIED}'",
        )
        count_denied = cursor.fetchone()[0]

        cursor.execute(
            f"SELECT COUNT(*) FROM {table_assignments}"
            f" WHERE status = '{consts.RULE_SETTING_STATUS_SELF_DISENROLLED}'",
        )
        count_self_disenrolled = cursor.fetchone()[0]

        cursor.execute(
            f"SELECT COUNT(DISTINCT {consts.COLUMN_NAME_ASSIGNMENTS_MATRICULE_NUMBER})"
            f" FROM {table_assignments}",
        )
        count_students = cursor.fetchone()[0]

        cursor.execute(
            f"SELECT COUNT(DISTINCT {consts.COLUMN_NAME_ASSIGNMENTS_STUDY_PROGRAM_ID})"
            f" FROM {table_assignments}",
        )
        count_study_programs = cursor.fetchone()[0]

        cursor.execute(
            f"SELECT COUNT(DISTINCT {consts.COLUMN_NAME_ASSIGNMENTS_LECTURE_ID})"
            f" FROM {table_assignments}",
        )
        count_lectures = cursor.fetchone()[0]

        cursor.execute(f"SELECT runde FROM {table_internal}")
        count_round = cursor.fetchone()[0]

    return (
        count_accepted,
        count_enrolled,
        count_denied,
        count_self_disenrolled,
        count_students,
        count_study_programs,
        count_round,
        count_lectures,
    )


page_heading = html.Div(
    [
        html.H2("Schritt 1: Übersicht der Belegwünsche"),
        html.P("Prüfen einzelner Daten vor der Simulation."),
        html.Hr(),
    ],
)


data_overview = html.Div(
    [
        dbc.Spinner(
            children=html.Div(id="spinner-sim-overview-info-loading"),
            size="md",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.P(id="text-sim-overview-count-programs"),
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        html.P(id="text-sim-overview-count-lectures"),
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        html.P(id="text-sim-overview-count-students"),
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        html.P(id="text-sim-overview-count-round"),
                    ],
                    width=3,
                ),
            ],
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.P(
                            id="text-sim-overview-count-assignment-enrolled",
                        ),
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        html.P(
                            id="text-sim-overview-count-assignment-accepted",
                        ),
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        html.P(id="text-sim-overview-count-assignment-denied"),
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        html.P(
                            id="text-sim-overview-count-assignment-self-disenrolled",
                        ),
                    ],
                    width=3,
                ),
            ],
        ),
    ],
)


grid = html.Div(
    [
        dag.AgGrid(
            id="ag-grid-sim-overview",
            className="ag-theme-alpine selection compact",
            dashGridOptions={"rowSelection": "single"},
            defaultColDef={"sortable": True},
            style={"height": "42vh"},
            columnSize="sizeToFit",
        ),
    ],
)


grid_buttons = html.Div(
    [
        dbc.Button(
            [
                dbc.Spinner(
                    html.Div(id="spinner-sim-overview-button-load"),
                    size="sm",
                ),
                " Liste neu laden",
            ],
            outline=True,
            color="secondary",
            class_name="mb-3",
            id="button-sim-overview-load",
        ),
        html.Div(id="text-sim-overview-table-max-entries"),
        html.Hr(className="mt-5"),
    ],
    className="mt-3",
)


page_navigation = html.Div(
    [
        dbc.Stack(
            [
                dbc.Button(
                    "Zurück",
                    href=consts.PAGE_DB_MANAGER_URL,
                    outline=True,
                    color="primary",
                    className="me-auto",
                ),
                dbc.Button(
                    "Weiter",
                    color="primary",
                    className="ms-auto",
                    id="button-sim-overview-next",
                ),
            ],
            direction="horizontal",
            className="mb-5",
        ),
    ],
)

sim_start_overview = html.Div(
    [
        dcc.Location(id="url-sim-overview"),
        page_heading,
        data_overview,
        grid,
        grid_buttons,
        page_navigation,
    ],
    className="page-container",
)

layout = dbc.Container(
    sim_start_overview,
    fluid=False,
    className="main-container",
)


@callback(
    [
        Output("ag-grid-sim-overview", "rowData"),
        Output("ag-grid-sim-overview", "columnDefs"),
        Output("spinner-sim-overview-button-load", "children"),
        Output("text-sim-overview-table-max-entries", "children"),
    ],
    [Input("button-sim-overview-load", "n_clicks")],
    [
        State("url-sim-overview", "search"),
    ],
)
def show_table_entries(n_clicks, search):
    """Update grid on pageload or when refresh button is clicked."""
    if n_clicks or consts.OVERVIEW_SETTING_AUTO_UPDATE:
        filename = file_utils.get_query_string(search, "filename")
        records, columnDefs = get_db_data_for_grid(filename)
        max_preview_size = consts.OVERVIEW_SETTING_MAX_PREVIEW_SIZE
        return (
            records,
            columnDefs,
            "",
            f"Die Tabellen-Vorschau ist derzeit auf {max_preview_size}"
            " Elemente limitiert. Dies kann in den Einstellungen geändert"
            " werden, wird aber auch zu längeren Ladezeiten oder"
            " Browserabstürzen führen.\nFür riesige Datensets bitte einen"
            " externen SQLite Datenbank Browser verwenden.",
        )
    return None, None, "", ""


@callback(
    Output("spinner-sim-overview-info-loading", "children"),
    Output("text-sim-overview-count-programs", "children"),
    Output("text-sim-overview-count-round", "children"),
    Output("text-sim-overview-count-lectures", "children"),
    Output("text-sim-overview-count-students", "children"),
    Output("text-sim-overview-count-assignment-accepted", "children"),
    Output("text-sim-overview-count-assignment-enrolled", "children"),
    Output("text-sim-overview-count-assignment-denied", "children"),
    Output("text-sim-overview-count-assignment-self-disenrolled", "children"),
    Input("url-sim-overview", "search"),
    Input("url-sim-overview", "pathname"),
)
def show_db_assignment_info(search, pathname):
    if search and pathname == consts.PAGE_SIM_START_URL:
        filename = file_utils.get_query_string(search, "filename")

        (
            count_accepted,
            count_enrolled,
            count_denied,
            count_self_disenrolled,
            count_students,
            count_study_programs,
            count_round,
            count_lectures,
        ) = get_db_assignment_info(filename)

        return (
            "",
            f"Anzahl Studiengänge: {count_study_programs}",
            f"Aktuelle Runde: {count_round}",
            f"Anzahl Veranstaltungen: {count_lectures}",
            f"Anzahl Studierende: {count_students}",
            f"Anzahl Zulassungen: {count_accepted}",
            f"Anzahl Anmeldungen: {count_enrolled}",
            f"Anzahl Ablehnungen: {count_denied}",
            f"Anzahl Selbstabmeldungen: {count_self_disenrolled}",
        )
    # Returning empty strings prevents error when switching pages
    return (
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
    )


@callback(
    Output("button-sim-overview-next", "disabled"),
    Output("button-sim-overview-next", "href"),
    Input("url-sim-overview", "search"),
)
def update_url_next_button_href(search):
    """Set query string href to filename already in query string."""
    if search:
        db_name = file_utils.get_query_string(search, "filename")
        return (
            False,
            f"{consts.PAGE_SIM_RULE_EDITOR_URL}?filename={db_name}",
        )

    return True, "/"


@callback(
    Output("url-sim-overview", "href"),
    Input("url-sim-overview", "search"),
    Input("url-sim-overview", "pathname"),
)
def redirect_when_missing_query_string(search, pathname):
    """Redirect to homepage if no query string is found."""
    if (
        not search
        and not file_utils.get_query_string(search, "filename")
        and pathname != consts.PAGE_SIM_RULE_EDITOR_URL
        and pathname != consts.PAGE_DB_MANAGER_URL
    ):
        logger.error(
            "Keine Datenbank-Angabe im Query-String gefunden! Bitte dem"
            " Programmablauf folgen und ab dem Datenbank-Manager starten",
        )
        return consts.PAGE_HOME_URL
