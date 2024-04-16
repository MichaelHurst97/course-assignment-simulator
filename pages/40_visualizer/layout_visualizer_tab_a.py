"""Accordion with information only regarding stat tab a."""

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html

import utils.constants as consts
from utils import file_utils

from .layout_visualizer_common_functions import (
    create_flex_piechart_figure,
    create_stat_tab,
    options_piechart_parameter,
    options_piechart_selector,
)
from .layout_visualizer_data_store import data_store

tab_overview_a = html.Div(id="div-stat-tab-a")

flex_piecharts_a = html.Div(
    [
        html.H5(id="piechart-flex-heading-a", className=("mt-5")),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Select(
                                        id="piechart-flex-parameter-a-l",
                                    ),
                                    width=4,
                                ),
                                dbc.Col(
                                    dbc.Select(
                                        id="piechart-flex-selector-a-l",
                                    ),
                                    width=6,
                                ),
                            ],
                        ),
                        dbc.Row(
                            [
                                dbc.Spinner(
                                    html.Div(id="spinner-piechart-flex-a-l"),
                                ),
                                dbc.Col(
                                    dcc.Graph(
                                        id="piechart-flex-a-l",
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
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Select(
                                        id="piechart-flex-parameter-a-r",
                                    ),
                                    width=4,
                                ),
                                dbc.Col(
                                    dbc.Select(
                                        id="piechart-flex-selector-a-r",
                                    ),
                                    width=6,
                                ),
                            ],
                        ),
                        dbc.Row(
                            [
                                dbc.Spinner(
                                    html.Div(id="spinner-piechart-flex-a-r"),
                                ),
                                dbc.Col(
                                    dcc.Graph(
                                        id="piechart-flex-a-r",
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

tab_a = html.Div(
    dbc.Accordion(
        [
            dbc.AccordionItem(
                [
                    tab_overview_a,
                    html.Hr(),
                    flex_piecharts_a,
                    html.Hr(),
                ],
                id="accordion-stat-tab-a",
                style={"display": "none"},
            ),
        ],
        start_collapsed=True,
    ),
)


@callback(
    Output("accordion-stat-tab-a", "style"),
    Output("accordion-stat-tab-a", "title"),
    Input("url-visualizer", "search"),
    Input("url-visualizer", "pathname"),
    Input("data-store-loaded-check", "hidden"),
)
def show_accordion_tab_a(
    search,
    pathname,
    data_store_loaded,
):
    """Show the tab accordion when data_store has loaded."""
    if search and pathname == consts.PAGE_VISUALIZER_URL and data_store_loaded:
        stat_name_a = file_utils.get_query_string(search, "stat_a")

        if stat_name_a:
            return {}, stat_name_a

    return {"display": "none"}, ""


@callback(
    Output("div-stat-tab-a", "children"),
    Input("data-store-loaded-check", "hidden"),
)
def create_stat_tab_a(data_store_loaded):
    """Create static tab elements via function."""
    if data_store_loaded:
        stat_tab = create_stat_tab(
            data_store["stat_name_a"],
            data_store["stat_info_a"],
            data_store["df_accepted_assignments_a"],
            data_store["df_denied_assignments_a"],
            data_store["df_accepted_lecture_combinations_a"],
            data_store["df_assignments_a"],
            data_store["df_all_new_assignments_a"],
        )
        return stat_tab

    return None


@callback(
    Output("piechart-flex-parameter-a-l", "options"),
    Output("piechart-flex-selector-a-l", "options"),
    Output("piechart-flex-parameter-a-l", "value"),
    Output("piechart-flex-selector-a-l", "value"),
    Output("piechart-flex-parameter-a-r", "options"),
    Output("piechart-flex-selector-a-r", "options"),
    Output("piechart-flex-parameter-a-r", "value"),
    Output("piechart-flex-selector-a-r", "value"),
    Output("piechart-flex-heading-a", "children"),
    Input("data-store-loaded-check", "hidden"),
)
def set_flex_piechart_options_a(data_store_loaded):
    """Define dropwdown options for both flex piecharts."""
    if data_store_loaded:
        return (
            options_piechart_parameter,
            options_piechart_selector,
            options_piechart_parameter[0],
            options_piechart_selector[0],
            options_piechart_parameter,
            options_piechart_selector,
            options_piechart_parameter[3],
            options_piechart_selector[0],
            "Flexible Dateneingabe"
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
    )


@callback(
    Output("piechart-flex-a-l", "figure"),
    Output("spinner-piechart-flex-a-l", "children"),
    Input("piechart-flex-parameter-a-l", "value"),
    Input("piechart-flex-selector-a-l", "value"),
    Input("data-store-loaded-check", "hidden"),
)
def create_flex_piechart_figure_tab_a_l(
    value_parameter_l,
    value_selector_l,
    data_store_loaded,
):
    """Create left flex piechart figure."""
    if value_selector_l and data_store_loaded:
        figure_l = create_flex_piechart_figure(
            value_parameter_l,
            value_selector_l,
            data_store["df_accepted_assignments_a"],
            data_store["df_denied_assignments_a"],
            data_store["df_accepted_lecture_combinations_a"],
            data_store["df_assignments_a"],
            data_store["df_all_new_assignments_a"],
            data_store["stat_info_a"]["database_filename"]
        )

        return figure_l, ""
    return None, ""


@callback(
    Output("piechart-flex-a-r", "figure"),
    Output("spinner-piechart-flex-a-r", "children"),
    Input("piechart-flex-parameter-a-r", "value"),
    Input("piechart-flex-selector-a-r", "value"),
    Input("data-store-loaded-check", "hidden"),
)
def create_flex_piechart_figures_tab_a(
    value_parameter_r,
    value_selector_r,
    data_store_loaded,
):
    """Create right flex piechart figure."""
    if value_selector_r and data_store_loaded:
        figure_r = create_flex_piechart_figure(
            value_parameter_r,
            value_selector_r,
            data_store["df_accepted_assignments_a"],
            data_store["df_denied_assignments_a"],
            data_store["df_accepted_lecture_combinations_a"],
            data_store["df_assignments_a"],
            data_store["df_all_new_assignments_a"],
            data_store["stat_info_a"]["database_filename"]
        )

        return figure_r, ""
    return None, ""
