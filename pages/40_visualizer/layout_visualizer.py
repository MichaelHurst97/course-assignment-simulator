"""Base UI layout for the visualizer.

Wraps and calls other visualizer layout files.
"""

import warnings
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, ctx, dcc, html

import utils.constants as consts
from utils import file_utils, rule_utils

from .layout_visualizer_data_store import loading_spinner
from .layout_visualizer_tab_a import tab_a
from .layout_visualizer_tab_b import tab_b
from .layout_visualizer_tab_comparison import tab_comparison
from .layout_visualizer_tab_overview import tab_overview

# Ignore FutureWarning from Pandas, triggered by internal Plotly Express Code
# which I have no control over
warnings.filterwarnings("ignore", category=FutureWarning)

dash.register_page(
    __name__,
    path=consts.PAGE_VISUALIZER_URL,
    title=consts.PAGE_VISUALIZER_TITLE_NAME,
    name=consts.PAGE_VISUALIZER_TITLE_NAME,
)

page_heading = html.Div(
    [
        html.H2("Visualisierungs-Tool"),
        html.P(
            "Die Simulations-Ergebnisse können hier geprüft und"
            " verglichen werden",
        ),
    ],
)

page_navigation = html.Div(
    [
        html.Hr(className="mt-3"),
        dbc.Stack(
            [
                dbc.Button(
                    "Zurück zur Startseite",
                    href=consts.PAGE_HOME_URL,
                    color="primary",
                    className="me-auto",
                    id="button-visualizer-back",
                ),
            ],
            direction="horizontal",
            className="mb-5",
        ),
    ],
)

stat_selection = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5("Statistik A: "),
                        dbc.Select(
                            id="select-visualizer-stat-a",
                            size="sm",
                        ),
                    ],
                    width=6,
                ),
                dbc.Col(
                    [
                        html.H5("Statistik B: "),
                        dbc.Select(
                            id="select-visualizer-stat-b",
                            size="sm",
                        ),
                    ],
                    width=6,
                ),
            ],
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                dbc.Button(
                                    "Statistiken laden",
                                    id="button-visualizer-load-stats",
                                    className="mt-3",
                                ),
                            ],
                            id="tooltip-trigger-visualizer-load-stats",
                        ),
                        dbc.Tooltip(
                            "Statistiken haben unterschiedliche"
                            " Datenbank-IDs. Bitte Regelsets auf den"
                            " gleichen / duplizierten Datenbank-Import"
                            " anwenden.",
                            placement="left",
                            target="tooltip-trigger-visualizer-load-stats",
                            id="tooltip-visualizer-load-stats-dbid",
                        ),
                        dbc.Tooltip(
                            "Statistiken haben unterschiedliche"
                            " Semester. Für einen Vergleich zweier Regelsets"
                            " mit derselben Datengrundlage sollten diese"
                            " gleich sein.",
                            placement="left",
                            target="tooltip-trigger-visualizer-load-stats",
                            id="tooltip-visualizer-load-stats-semester",
                        ),
                    ],
                    width=3,
                ),
            ],
        ),
    ],
)


visualizer = html.Div(
    [
        loading_spinner,
        dcc.Location(id="url-visualizer"),
        dcc.Store(id="store-visualizer"),
        page_heading,
        stat_selection,
        tab_overview,
        tab_a,
        tab_b,
        tab_comparison,
        page_navigation,
        html.Div(id="data-store-loaded-check", hidden=False),
    ],
    className="page-container",
)


layout = html.Div(
    [
        dbc.Container(visualizer, fluid=False, className="main-container"),
    ],
)


@callback(
    Output("button-visualizer-load-stats", "disabled"),
    Output("select-visualizer-stat-a", "options"),
    Output("select-visualizer-stat-b", "options"),
    Output("tooltip-visualizer-load-stats-dbid", "style"),
    Output("tooltip-visualizer-load-stats-semester", "style"),
    Input("url-visualizer", "search"),
    Input("select-visualizer-stat-a", "value"),
    Input("select-visualizer-stat-b", "value"),
)
def toggle_button_load_stats(search, stat_a, stat_b):
    """Activate the load button if only stat a is selected
    or stat a and b database ids match.

    """
    stat_list = rule_utils.get_stat_filelist()
    stat_list.insert(0, "")

    # Use to unhide tooltip, showing why stat comparison
    # shouldn't be made
    show_tooltip_id_mismatch = {"display": "none"}
    show_tooltip_semester_mismatch = {"display": "none"}

    if stat_a and stat_b:
        # Load stat info json files
        stat_folder_a = file_utils.get_folder(
            Path(consts.FOLDER_STAT_FILES, stat_a),
        )
        stat_info_a = file_utils.read_json(
            stat_folder_a,
            consts.FILENAME_STAT_INFO,
        )

        stat_folder_b = file_utils.get_folder(
            Path(consts.FOLDER_STAT_FILES, stat_b),
        )
        stat_info_b = file_utils.read_json(
            stat_folder_b,
            consts.FILENAME_STAT_INFO,
        )

        # Determine if database ids and semester
        # match to make tooltip visible if not
        load_button_disabled_db_id = (
            stat_info_a["database_id"] != stat_info_b["database_id"]
        )
        load_button_disabled_semester = (
            stat_info_a["assignment_semester"]
            != stat_info_b["assignment_semester"]
        )

        # Show tooltip for mismatch in db id
        if load_button_disabled_db_id:
            show_tooltip_id_mismatch = {}

        # Show tooltip for mismatch in semester
        elif load_button_disabled_semester:
            show_tooltip_semester_mismatch = {}

        return (
            load_button_disabled_db_id or load_button_disabled_semester,
            stat_list,
            stat_list,
            show_tooltip_id_mismatch,
            show_tooltip_semester_mismatch,
        )

    elif stat_a:
        return (
            False,
            stat_list,
            stat_list,
            show_tooltip_id_mismatch,
            show_tooltip_semester_mismatch,
        )

    # No selection
    return (
        True,
        stat_list,
        "",
        show_tooltip_id_mismatch,
        show_tooltip_semester_mismatch,
    )


@callback(
    Output("url-visualizer", "href"),
    Input("button-visualizer-load-stats", "n_clicks"),
    Input("select-visualizer-stat-a", "value"),
    Input("select-visualizer-stat-b", "value"),
)
def trigger_page_reload_to_load_stats(
    n_clicks,
    value_stat_dropwdown_a,
    value_stat_dropwdown_b,
):
    """Reload the page with query string in url.

    load_stats_into_store() triggers the actual stat loading.
    """
    if (
        n_clicks
        and value_stat_dropwdown_a
        and ctx.triggered_id == "button-visualizer-load-stats"
    ):
        # Get current dropdown values and create a query string
        search = f"stat_a={value_stat_dropwdown_a}"
        if value_stat_dropwdown_b:
            search = f"{search}&stat_b={value_stat_dropwdown_b}"

        return f"{consts.PAGE_VISUALIZER_URL}?{search}"

    return None


@callback(
    Output("select-visualizer-stat-a", "value"),
    Output("select-visualizer-stat-b", "value"),
    Input("url-visualizer", "search"),
    Input("url-visualizer", "pathname"),
)
def update_loaded_select_stat_value(
    search,
    pathname,
):
    """Update the dropdown values to select the current stats via url."""
    if search and pathname == consts.PAGE_VISUALIZER_URL:
        stat_name_a = file_utils.get_query_string(search, "stat_a")
        stat_name_b = file_utils.get_query_string(search, "stat_b")

        return stat_name_a, stat_name_b

    return None, None
