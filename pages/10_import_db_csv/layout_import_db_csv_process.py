"""UI layout for the process of importing CSV files."""

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html

import utils.constants as consts
from utils import file_utils
from utils.logger import logger

from . import model_import_db_csv

dash.register_page(
    __name__,
    path=consts.PAGE_IMPORT_DB_FILE_PROCESS_URL,
    title=consts.PAGE_IMPORT_DB_FILE_PROCESS_TITLE_NAME,
    name=consts.PAGE_IMPORT_DB_FILE_PROCESS_TITLE_NAME,
)

page_heading = html.Div(
    [
        html.H2("Import im Gange...", id="heading-import-process"),
        html.P(
            "Bitte warten und Seite nicht verlassen.",
            id="subheading-import-process",
        ),
        html.Hr(),
    ],
)


import_log = html.Div(
    [
        dcc.Interval(
            id="interval-import",
            interval=1000,
            n_intervals=0,
        ),
        dcc.Textarea(
            id="log-import",
            style={"width": "100%", "height": "55vh"},
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
                    [
                        dbc.Spinner(size="sm"),
                        " Importiere...",
                    ],
                    id="button-import-process-next",
                    className="ms-auto",
                    color="primary",
                    disabled=True,
                    href=consts.PAGE_HOME_URL,
                ),
            ],
            direction="horizontal",
            gap=3,
            className="mb-5",
        ),
        html.Hr(),
    ],
)


layout_import_db_file = html.Div(
    [
        dcc.Location(id="url-import-process"),
        page_heading,
        import_log,
        page_navigation,
    ],
    className="page-container",
)

layout = dbc.Container(
    layout_import_db_file,
    fluid=False,
    className="main-container",
)


@callback(
    [
        Output("button-import-process-next", "disabled"),
        Output("button-import-process-next", "children"),
        Output("interval-import", "disabled"),
        Output("heading-import-process", "children"),
        Output("subheading-import-process", "children"),
    ],
    Input("url-import-process", "search"),
)
def run_import(search: str):
    """Execute the import function."""
    if search:
        filename = file_utils.get_query_string(search, "filename")
        # None as filename for import_csv_files() means that it will
        # assemble it's own filename based on datetime
        filename = None if filename == "default" else filename
        import_success = model_import_db_csv.import_csv_files(filename)

        if import_success:
            return (
                False,
                [
                    html.I(className="bi bi-check-circle-fill me-2"),
                    "Zur Startseite",
                ],
                False,
                "Import fertiggestellt!",
                "Seite kann verlassen werden.",
            )
        else:
            return (
                False,
                [
                    html.I(className="bi bi-x-octagon-fill me-2"),
                    "Zur Startseite",
                ],
                True,
                "Import fehlgeschlagen",
                "Seite kann verlassen werden.",
            )
    return True, "", True, "", ""


@callback(
    Output("log-import", "disabled"),
    Input("url-import-process", "search"),
)
def clear_log(search):
    """Clear the log on pageload."""
    logger.log_stream.truncate(0)
    logger.log_stream.seek(0)

    return False


@callback(
    Output("log-import", "value"),
    Input("interval-import", "n_intervals"),
)
def update_log(_):
    """Update the log shown in the textarea in intervals."""
    content = logger.log_stream.getvalue()
    content = content.replace(consts.CONSOLE_GREEN, "")
    content = content.replace(consts.CONSOLE_BLUE, "")
    content = content.replace(consts.CONSOLE_RED, "")
    content = content.replace(consts.CONSOLE_YELLOW, "")
    content = content.replace(consts.CONSOLE_ENDCMD, "")

    return content


@callback(
    Output("url-import-process", "href"),
    Input("url-import-process", "search"),
    Input("url-import-process", "pathname"),
)
def redirect_when_missing_query_string(search: str, pathname: str):
    """Redirect to home page when query string for db filename is missing."""
    if (
        pathname != consts.PAGE_DB_MANAGER_URL
        and not file_utils.get_query_string(search, "filename")):
        logger.error(
            "Keine Datenbank Angabe im Query String gefunden!"
            f" Bitte dem Programmablauf folgen. Query-String: '{search}'",
        )
        return consts.PAGE_HOME_URL
    return None
