"""Accordion with information only regarding stat tab b.

Differs in ID's and texts from stat tab a and only is shown
when stat b is in url.
Unreasonable to be solved programmatically layout-wise.
"""

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

tab_overview_b = html.Div(id="div-stat-tab-b")

flex_piecharts_b = html.Div(
    [
        html.H5(id="piechart-flex-heading-b", className=("mt-5")),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Select(
                                        id="piechart-flex-parameter-b-l",
                                    ),
                                    width=4,
                                ),
                                dbc.Col(
                                    dbc.Select(
                                        id="piechart-flex-selector-b-l",
                                    ),
                                    width=6,
                                ),
                            ],
                        ),
                        dbc.Row(
                            [
                                dbc.Spinner(
                                    html.Div(id="spinner-piechart-flex-b-l"),
                                ),
                                dbc.Col(
                                    dcc.Graph(
                                        id="piechart-flex-b-l",
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
                                        id="piechart-flex-parameter-b-r",
                                    ),
                                    width=4,
                                ),
                                dbc.Col(
                                    dbc.Select(
                                        id="piechart-flex-selector-b-r",
                                    ),
                                    width=6,
                                ),
                            ],
                        ),
                        dbc.Row(
                            [
                                dbc.Spinner(
                                    html.Div(id="spinner-piechart-flex-b-r"),
                                ),
                                dbc.Col(
                                    dcc.Graph(
                                        id="piechart-flex-b-r",
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

tab_b = html.Div(
    dbc.Accordion(
        [
            dbc.AccordionItem(
                [
                    tab_overview_b,
                    html.Hr(),
                    flex_piecharts_b,
                    html.Hr(),
                ],
                id="accordion-stat-tab-b",
                style={"display": "none"},
            ),
        ],
        start_collapsed=True,
        className="mt-3",
    ),
)


@callback(
    Output("accordion-stat-tab-b", "style"),
    Output("accordion-stat-tab-b", "title"),
    Input("url-visualizer", "search"),
    Input("url-visualizer", "pathname"),
    Input("data-store-loaded-check", "hidden"),
)
def show_accordion_tab_b(
    search,
    pathname,
    data_store_loaded,
):
    """Show the tab accordion when data_store has loaded and if stat b is
    found in query string.
    """
    if search and pathname == consts.PAGE_VISUALIZER_URL and data_store_loaded:
        stat_name_b = file_utils.get_query_string(search, "stat_b")

        if stat_name_b:
            return {}, stat_name_b

    return {"display": "none"}, ""


@callback(
    Output("div-stat-tab-b", "children"),
    Input("url-visualizer", "search"),
    Input("url-visualizer", "pathname"),
    Input("data-store-loaded-check", "hidden"),
)
def create_stat_tab_b(
    search,
    pathname,
    data_store_loaded,
):
    """Create static tab elements via function."""
    if search and pathname == consts.PAGE_VISUALIZER_URL and data_store_loaded:
        stat_name_b = file_utils.get_query_string(search, "stat_b")

        if stat_name_b:
            stat_tab = create_stat_tab(
                data_store["stat_name_b"],
                data_store["stat_info_b"],
                data_store["df_accepted_assignments_b"],
                data_store["df_denied_assignments_b"],
                data_store["df_accepted_lecture_combinations_b"],
                data_store["df_assignments_b"],
                data_store["df_all_new_assignments_b"],
            )
            return stat_tab

    return None


@callback(
    Output("piechart-flex-parameter-b-l", "options"),
    Output("piechart-flex-selector-b-l", "options"),
    Output("piechart-flex-parameter-b-l", "value"),
    Output("piechart-flex-selector-b-l", "value"),
    Output("piechart-flex-parameter-b-r", "options"),
    Output("piechart-flex-selector-b-r", "options"),
    Output("piechart-flex-parameter-b-r", "value"),
    Output("piechart-flex-selector-b-r", "value"),
    Output("piechart-flex-heading-b", "children"),
    Input("data-store-loaded-check", "hidden"),
)
def set_flex_piechart_options_b(data_store_loaded):
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
    Output("piechart-flex-b-l", "figure"),
    Output("spinner-piechart-flex-b-l", "children"),
    Input("piechart-flex-parameter-b-l", "value"),
    Input("piechart-flex-selector-b-l", "value"),
    Input("url-visualizer", "search"),
    Input("url-visualizer", "pathname"),
    Input("data-store-loaded-check", "hidden"),
)
def create_flex_piechart_figure_tab_b_l(
    value_parameter_l,
    value_selector_l,
    search,
    pathname,
    data_store_loaded,
):
    """Create left flex piechart figure."""
    if (
        value_selector_l
        and search
        and pathname == consts.PAGE_VISUALIZER_URL
        and data_store_loaded
    ):
        stat_name_b = file_utils.get_query_string(search, "stat_b")

        if stat_name_b:
            figure_l = create_flex_piechart_figure(
                value_parameter_l,
                value_selector_l,
                data_store["df_accepted_assignments_b"],
                data_store["df_denied_assignments_b"],
                data_store["df_accepted_lecture_combinations_b"],
                data_store["df_assignments_b"],
                data_store["df_all_new_assignments_b"],
                data_store["stat_info_b"]["database_filename"]
            )

            return figure_l, ""
    return None, ""


@callback(
    Output("piechart-flex-b-r", "figure"),
    Output("spinner-piechart-flex-b-r", "children"),
    Input("piechart-flex-parameter-b-r", "value"),
    Input("piechart-flex-selector-b-r", "value"),
    Input("url-visualizer", "search"),
    Input("url-visualizer", "pathname"),
    Input("data-store-loaded-check", "hidden"),
)
def create_flex_piechart_figure_tab_b_r(
    value_parameter_r,
    value_selector_r,
    search,
    pathname,
    data_store_loaded,
):
    """Create right flex piechart figure."""
    if (
        value_selector_r
        and search
        and pathname == consts.PAGE_VISUALIZER_URL
        and data_store_loaded
    ):
        stat_name_b = file_utils.get_query_string(search, "stat_b")

        if stat_name_b:
            figure_r = create_flex_piechart_figure(
                value_parameter_r,
                value_selector_r,
                data_store["df_accepted_assignments_b"],
                data_store["df_denied_assignments_b"],
                data_store["df_accepted_lecture_combinations_b"],
                data_store["df_assignments_b"],
                data_store["df_all_new_assignments_b"],
                data_store["stat_info_b"]["database_filename"]
            )

            return figure_r, ""
    return None, ""
