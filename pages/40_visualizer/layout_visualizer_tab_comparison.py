"""Accordion that has multiple charts showing stat comparisons."""

import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

import utils.constants as consts
from utils import file_utils
from utils import layout_utils

from .layout_visualizer_common_functions import (
    create_flex_piechart_figure,
    options_piechart_parameter,
    options_piechart_selector,
)
from .layout_visualizer_data_store import data_store

barchart_rule_comparison = html.Div(
    [
        html.H5("Anzahl Belegungen pro Regel"),
        dcc.Graph(id="barchart-rule-comparison"),
    ],
)

flex_barchart_comparison = html.Div(
    [
        html.H5(
            "Flexible Dateneingabe - gemeinsame Chart -"
            " Belegungen mit neuem Status"
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Select(
                        id="barchart-flex-selector-comparison",
                    ),
                    width=4,
                ),
            ],
        ),
        dbc.Row(
            [
                dbc.Spinner(html.Div(id="spinner-barchart-flex-comparison")),
                dbc.Col(
                    dcc.Graph(id="barchart-flex-comparison"),
                    width=12,
                ),
            ],
        ),
    ],
)

flex_piecharts_comparison = html.Div(
    [
        html.H5(
            "Flexible Dateneingabe - Charts nebeneinander",
            className=("mt-5 mb-4"),
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5(id="piechart-flex-heading-l"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Select(
                                        id="piechart-flex-parameter-comparison-l",
                                    ),
                                    width=4,
                                ),
                                dbc.Col(
                                    dbc.Select(
                                        id="piechart-flex-selector-comparison-l",
                                    ),
                                    width=6,
                                ),
                            ],
                        ),
                        dbc.Row(
                            [
                                dbc.Spinner(
                                    html.Div(
                                        id="spinner-piechart-flex-comparison-l",
                                    ),
                                ),
                                dbc.Col(
                                    dcc.Graph(
                                        id="piechart-flex-comparison-l",
                                    ),
                                    width=12,
                                ),
                            ],
                            className="mt-2",
                        ),
                    ],
                    width=6,
                ),
                dbc.Col(
                    [
                        html.H5(id="piechart-flex-heading-r"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Select(
                                        id="piechart-flex-parameter-comparison-r",
                                    ),
                                    width=4,
                                ),
                                dbc.Col(
                                    dbc.Select(
                                        id="piechart-flex-selector-comparison-r",
                                    ),
                                    width=6,
                                ),
                            ],
                        ),
                        dbc.Row(
                            [
                                dbc.Spinner(
                                    html.Div(
                                        id="spinner-piechart-flex-comparison-r",
                                    ),
                                ),
                                dbc.Col(
                                    dcc.Graph(
                                        id="piechart-flex-comparison-r",
                                    ),
                                    width=12,
                                ),
                            ],
                            className="mt-2",
                        ),
                    ],
                    width=6,
                ),
            ],
        ),
    ],
)

tab_comparison = html.Div(
    dbc.Accordion(
        [
            dbc.AccordionItem(
                [
                    barchart_rule_comparison,
                    html.Hr(),
                    flex_barchart_comparison,
                    html.Hr(),
                    flex_piecharts_comparison,
                    html.Hr(),
                ],
                title="Vergleich beider Statistiken",
                id="accordion-stat-tab-comparison",
                style={"display": "none"},
            ),
        ],
        start_collapsed=True,
        className="mt-3",
    ),
)


@callback(
    Output("accordion-stat-tab-comparison", "style"),
    Input("url-visualizer", "search"),
    Input("url-visualizer", "pathname"),
    Input("data-store-loaded-check", "hidden"),
)
def show_accordion_tab_comparison(
    search,
    pathname,
    data_store_loaded,
):
    """Show the comparison accordion when data_store has loaded and if both stats are
    found in query string.
    """
    if search and pathname == consts.PAGE_VISUALIZER_URL and data_store_loaded:
        stat_name_a = file_utils.get_query_string(search, "stat_a")
        stat_name_b = file_utils.get_query_string(search, "stat_b")

        if stat_name_a and stat_name_b:
            return {}

    return {"display": "none"}


@callback(
    Output("barchart-rule-comparison", "figure"),
    Input("url-visualizer", "search"),
    Input("url-visualizer", "pathname"),
    Input("data-store-loaded-check", "hidden"),
)
def create_barchart_figure_rule_comparison(
    search,
    pathname,
    data_store_loaded,
):
    """Create a barchart figure showing count of statuses per rule."""
    if search and pathname == consts.PAGE_VISUALIZER_URL and data_store_loaded:
        stat_name_a = file_utils.get_query_string(search, "stat_a")
        stat_name_b = file_utils.get_query_string(search, "stat_b")

        if stat_name_a and stat_name_b:
            df_all_new_assignments_a_b = data_store[
                "df_all_new_assignments_a_b"
            ]

            # Group status and rule number
            assignments_per_rule = (
                df_all_new_assignments_a_b.groupby(
                    ["sortierwert", "status", "Statistik"],
                )
                .size()
                .reset_index(name="Anzahl")
                .copy()
            )

            assignments_per_rule = assignments_per_rule.sort_values(
                by=["Statistik", "status"], ascending=True
            )

            assignments_per_rule["text"] = (
                assignments_per_rule["status"]
                + ": "
                + assignments_per_rule["Anzahl"].astype(str)
            )

            figure = go.Figure(
                layout=dict(template=consts.VISU_SETTING_PLOTLY_THEME),
            )
            figure = px.bar(
                assignments_per_rule,
                x="sortierwert",
                labels={"sortierwert": "Regelwert"},
                y="Anzahl",
                color="Statistik",
                barmode="group",
                text="text",
                color_discrete_sequence=px.colors.qualitative.D3,
            )
            figure.update_traces(textposition="inside")

            return figure

    return None


@callback(
    Output("barchart-flex-selector-comparison", "options"),
    Output("barchart-flex-selector-comparison", "value"),
    Input("url-visualizer", "search"),
    Input("url-visualizer", "pathname"),
)
def set_flex_barchart_options_comparison(search, pathname):
    """Define dropwdown options for flex barchart."""
    if search and pathname == consts.PAGE_VISUALIZER_URL:
        stat_name_a = file_utils.get_query_string(search, "stat_a")
        stat_name_b = file_utils.get_query_string(search, "stat_b")

        if stat_name_a and stat_name_b:
            options_parameter = [
                "Fachsemester",
                "Studiengänge",
                "Gruppen",
                "Erstbelegungen",
                "Hörerstatus",
                "Studiumsart",
                "Studiumstyp",
            ]

            return (
                options_parameter,
                "Fachsemester",
            )

    return (
        None,
        "",
    )


@callback(
    Output("barchart-flex-comparison", "figure"),
    Output("spinner-barchart-flex-comparison", "children"),
    Input("barchart-flex-selector-comparison", "value"),
    Input("data-store-loaded-check", "hidden"),
)
def create_flex_barchart_comparison_figure(value_selector, data_store_loaded):
    """Create a barchart figure with user chosen data."""
    if value_selector and data_store_loaded:
        df_all_new_assignments_a_b = data_store["df_all_new_assignments_a_b"]

        if value_selector == "Fachsemester":
            column = "fachsemester"
        elif value_selector == "Studiengänge":
            column = "studiengangs_id"
        elif value_selector == "Gruppen":
            column = "gruppen_id"
        elif value_selector == "Erstbelegungen":
            column = "erstbelegung"
        elif value_selector == "Hörerstatus":
            column = "hoererstatus"
        elif value_selector == "Studiumsart":
            column = "studiumsart"
        elif value_selector == "Studiumstyp":
            column = "studiumstyp"

        df_all_new_assignments_a_b = layout_utils.expand_db_value_names(
            df_all_new_assignments_a_b,
            column,
            data_store["stat_info_a"]["database_filename"],
        )

        df_all_new_assignments_a_b = (
            df_all_new_assignments_a_b.groupby([column, "status", "Statistik"])
            .size()
            .reset_index(name="Anzahl")
            .copy()
        )

        df_all_new_assignments_a_b = df_all_new_assignments_a_b.sort_values(
            by=["Statistik", "status"], ascending=True
        )

        df_all_new_assignments_a_b["text"] = (
            df_all_new_assignments_a_b["status"]
            + ": "
            + df_all_new_assignments_a_b["Anzahl"].astype(str)
        )

        figure = px.bar(
            df_all_new_assignments_a_b,
            x=column,
            labels={value_selector: column},
            y="Anzahl",
            color="Statistik",  # Use the new column for color
            barmode="group",
            template=consts.VISU_SETTING_PLOTLY_THEME,
            text="text",
            color_discrete_sequence=px.colors.qualitative.Bold,
            height = 500
        )
        figure.update_traces(textposition="inside")

        return figure, ""
    return None, ""


@callback(
    Output("piechart-flex-parameter-comparison-l", "options"),
    Output("piechart-flex-selector-comparison-l", "options"),
    Output("piechart-flex-parameter-comparison-l", "value"),
    Output("piechart-flex-selector-comparison-l", "value"),
    Output("piechart-flex-parameter-comparison-r", "options"),
    Output("piechart-flex-selector-comparison-r", "options"),
    Output("piechart-flex-parameter-comparison-r", "value"),
    Output("piechart-flex-selector-comparison-r", "value"),
    Output("piechart-flex-heading-l", "children"),
    Output("piechart-flex-heading-r", "children"),
    Input("url-visualizer", "search"),
    Input("url-visualizer", "pathname"),
)
def set_flex_piechart_comparison_options(search, pathname):
    """Define dropwdown options for both flex piecharts."""
    if search and pathname == consts.PAGE_VISUALIZER_URL:
        stat_name_a = file_utils.get_query_string(search, "stat_a")
        stat_name_b = file_utils.get_query_string(search, "stat_b")

        if stat_name_a and stat_name_b:
            return (
                options_piechart_parameter,
                options_piechart_selector,
                options_piechart_parameter[0],
                options_piechart_selector[2],
                options_piechart_parameter,
                options_piechart_selector,
                options_piechart_parameter[0],
                options_piechart_selector[2],
                stat_name_a,
                stat_name_b,
            )

    return (
        None,
        None,
        "",
        "",
        None,
        None,
        "",
        "",
        "",
        "",
    )


@callback(
    Output("piechart-flex-comparison-l", "figure"),
    Output("spinner-piechart-flex-comparison-l", "children"),
    Input("piechart-flex-parameter-comparison-l", "value"),
    Input("piechart-flex-selector-comparison-l", "value"),
    Input("data-store-loaded-check", "hidden"),
)
def create_flex_piechart_figure_comparison_l(
    value_parameter,
    value_selector,
    data_store_loaded,
):
    if value_selector and data_store_loaded:
        """Create left flex piechart figure, for stat a."""
        figure = create_flex_piechart_figure(
            value_parameter,
            value_selector,
            data_store["df_accepted_assignments_a"],
            data_store["df_denied_assignments_a"],
            data_store["df_accepted_lecture_combinations_a"],
            data_store["df_assignments_a"],
            data_store["df_all_new_assignments_a"],
            data_store["stat_info_a"]["database_filename"],
        )

        return figure, ""

    return None, ""


@callback(
    Output("piechart-flex-comparison-r", "figure"),
    Output("spinner-piechart-flex-comparison-r", "children"),
    Input("piechart-flex-parameter-comparison-r", "value"),
    Input("piechart-flex-selector-comparison-r", "value"),
    Input("data-store-loaded-check", "hidden"),
)
def create_flex_piechart_figure_comparison_r(
    value_parameter,
    value_selector,
    data_store_loaded,
):
    if value_selector and data_store_loaded:
        """Create right flex piechart figure, for stat b."""
        figure = create_flex_piechart_figure(
            value_parameter,
            value_selector,
            data_store["df_accepted_assignments_b"],
            data_store["df_denied_assignments_b"],
            data_store["df_accepted_lecture_combinations_b"],
            data_store["df_assignments_b"],
            data_store["df_all_new_assignments_b"],
            data_store["stat_info_b"]["database_filename"],
        )

        return figure, ""
    return None, ""
