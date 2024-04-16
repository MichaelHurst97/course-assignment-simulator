"""Functions that are shared between layout files."""

import warnings

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html

import utils.constants as consts
from utils import layout_utils

# Ignore FutureWarning from Pandas, triggered by internal Plotly Express Code which I have no control over
warnings.filterwarnings("ignore", category=FutureWarning)


options_piechart_parameter = [
    "Anzahl Belegungen pro Status",
    "Fachsemester",
    "Studiengänge",
    "Veranstaltungen",
    "Gruppen",
    "Erstbelegungen",
    "Hörerstatus",
    "Studiumsart",
    "Studiumstyp",
]

options_piechart_selector = [
    "für neue Zulassungen",
    "für neue Ablehnungen",
    "für neue Zulassungen und Ablehnungen",
    "für neue Kombinationseinschreibungen",
    "für ausstehende Anmeldungen",
    "für insgesamt getätigte Selbstabmeldungen",
    "für gesamtes Semester und Vorselektion",
]


def create_stat_tab_overview(df_assignments):
    return html.Div(
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.P(
                            f"Belegungseinträge gesamt: {len(df_assignments)}",
                        ),
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        html.P(
                            f"Studierende gesamt: {df_assignments["matrikelnummer"].nunique()}",
                        ),
                    ],
                    width=2,
                ),
                dbc.Col(
                    [
                        html.P(
                            f"Studiengänge gesamt: {df_assignments["studiengangs_id"].nunique()}",
                        ),
                    ],
                    width=2,
                ),
                dbc.Col(
                    [
                        html.P(
                            f"Vorlesungen gesamt: {df_assignments["veranstaltungs_id"].nunique()}",
                        ),
                    ],
                    width=2,
                ),
                dbc.Col(
                    [
                        html.P(
                            f"Gruppen gesamt: {df_assignments["gruppen_id"].nunique()}",
                        ),
                    ],
                    width=2,
                ),
            ],
        ),
    )


def get_rule_elements(rule: list):
    """Split up rule from stat dict into seperate elements."""
    if rule:
        return (
            rule[0],
            rule[1],
            rule[2],
            rule[3],
            rule[4],
        )
    else:
        return None, None, None, None, None


def create_rule_grid(stat_info: dict):
    """Create an ag-grid to display a ruleset."""
    rowData = []
    count = 1
    for rule in stat_info["ruleset_rules_assignment"]:
        (
            tabelle_l,
            spalte_l,
            operator,
            tabelle_r,
            spalte_r,
        ) = get_rule_elements(rule["rule_assignment"])
        (
            tabelle_l2,
            spalte_l2,
            operator2,
            tabelle_r2,
            spalte_r2,
        ) = get_rule_elements(rule["rule_assignment_2"])

        # Check if rule compares to loose value
        if tabelle_r is None:
            tabelle_r = "Freie Eingabe"

        if tabelle_r2 is None:
            tabelle_r2 = "Freie Eingabe"

        row = {
            "Nr": count,
            "Name": rule["rule_name"],
            "Tabelle L": tabelle_l,
            "Spalte L": spalte_l,
            "Operator": operator,
            "Tabelle R": tabelle_r,
            "Spalte R": spalte_r,
            "Log Op": rule["rule_join_operation"],
            "Tabelle L2": tabelle_l2,
            "Spalte L2": spalte_l2,
            "Operator2": operator2,
            "Tabelle R2": tabelle_r2,
            "Spalte R2": spalte_r2,
        }
        count += 1
        rowData.append(row)

    columnDefs = [
        {"field": "Nr", "width": 70},
        {"field": "Name", "width": 200},
        {"field": "Tabelle L", "width": 120},
        {"field": "Spalte L", "width": 120},
        {"field": "Operator", "width": 100},
        {"field": "Tabelle R", "width": 120},
        {"field": "Spalte R", "width": 120},
        {"field": "Log Op", "width": 100},
        {"field": "Tabelle L2", "width": 120},
        {"field": "Spalte L2", "width": 120},
        {"field": "Operator2", "width": 100},
        {"field": "Tabelle R2", "width": 120},
        {"field": "Spalte R2", "width": 120},
    ]

    # Check if preselection exists
    if stat_info["ruleset_rule_preselection"] is not None:
        pinned_data = {
            "Nr": 0,
            "Name": "Vorselektion",
            "Tabelle L": stat_info["ruleset_rule_preselection"][0],
            "Spalte L": stat_info["ruleset_rule_preselection"][1],
            "Operator": stat_info["ruleset_rule_preselection"][2],
            "Tabelle R": stat_info["ruleset_rule_preselection"][3],
            "Spalte R": stat_info["ruleset_rule_preselection"][4],
        }
    else:
        pinned_data = {
            "Nr": 0,
            "Name": "Vorselektion",
            "Tabelle L": None,
            "Spalte L": None,
            "Operator": None,
            "Tabelle R": None,
            "Spalte R": None,
        }

    grid = dag.AgGrid(
        id="grid-rule-editor",
        className="ag-theme-alpine selection",
        columnDefs=columnDefs,
        rowData=rowData,
        dashGridOptions={
            "sortable": False,
            "pinnedTopRowData": [
                pinned_data,
            ],
        },
        defaultColDef={
            "sortable": False,
            "suppressMovable": True,
            "resizable": True,
        },
        style={"height": "50vh", "width": "100%"},
        getRowId="params.data.Nr",
    )

    return grid


def create_stat_tab_figure_new_assignments(new_assignments):
    # Preassign figure to prevent "invalid value" plotly bug
    figure_bar_new_assignments = go.Figure(
        layout={"template": consts.VISU_SETTING_PLOTLY_THEME},
    )
    figure_bar_new_assignments = px.bar(
        pd.DataFrame(new_assignments),
        x="Status",
        y="Anzahl",
        labels={"Anzahl": "Anzahl", "Status": "Status"},
        text_auto=True,
        template=consts.VISU_SETTING_PLOTLY_THEME,
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    return figure_bar_new_assignments


def round_mean_df_column(df, column):
    if df.empty:
        return None
    df = df.dropna(subset=[column])
    return round(df[column].mean(), 2) if not df.empty else None


def create_stat_tab_figure_mean_study_semester(new_assignments):
    figure_bar_mean_study_semester = go.Figure(
        layout={"template": consts.VISU_SETTING_PLOTLY_THEME},
    )
    figure_bar_mean_study_semester = px.bar(
        pd.DataFrame(new_assignments),
        x="Status",
        y="Ø Fachsemester",
        labels={"Ø Fachsemester": "Ø Fachsemester", "Status": "Status"},
        text_auto=True,
        template=consts.VISU_SETTING_PLOTLY_THEME,
        color_discrete_sequence=px.colors.qualitative.Bold,
    )

    return figure_bar_mean_study_semester


def create_stat_tab(
    stat_name: str,
    stat_info: dict,
    df_accepted_assignments,
    df_denied_assignments,
    df_accepted_lecture_combinations,
    df_assignments,
    df_all_new_assignments,
):
    """Assemble a stat tab containing information that doesn't change after
    it's created.

    Flex piecharts of the stat tab are not implemented in this function because
    their data needs to be loaded dynamically via user input.
    """

    overview = create_stat_tab_overview(df_assignments)

    ruleset_name = html.P(f"Regelset: {stat_info['ruleset_filename']}")

    ruleset_accordion = dbc.Accordion(
        [
            dbc.AccordionItem(
                [create_rule_grid(stat_info)],
                title="Belegungs-Regeln:",
            ),
        ],
        start_collapsed=True,
    )

    data_new_assignments = {
        "Status": [
            "Neue Zulassungen",
            "Neue Ablehnungen",
            "Neue Kombinationszulassungen",
            "Ausstehende Anmeldungen",
            "Insgesamt getätigte Selbstabmeldungen",
        ],
        "Anzahl": [
            len(df_accepted_assignments),
            len(df_denied_assignments),
            len(df_accepted_lecture_combinations),
            len(
                df_assignments[
                    df_assignments["status"]
                    == consts.RULE_SETTING_STATUS_ENROLLED
                ],
            ),
            len(
                df_assignments[
                    df_assignments["status"]
                    == consts.RULE_SETTING_STATUS_SELF_DISENROLLED
                ],
            ),
        ],
    }

    graph_new_assignments_per_status = html.Div(
        [
            html.H5(
                "Anzahl neuer Belegungen pro Status",
                id="heading-status-tab-overview",
                className=("mt-5"),
            ),
            dbc.Tooltip(
                "Hinweis: Die Anzahl bezieht sich auf die Belegungen mit neuem"
                " Status in dieser Simulations-Runde. Selbstabmeldungen sind"
                " jedoch als Gesamtanzzahl für das aktuelle Semester und die"
                " aktuelle Vorselektion angegeben und dienen daher zum Abgleich.",
                target="heading-status-tab-overview",
                placement="top",
            ),
            dcc.Graph(
                figure=create_stat_tab_figure_new_assignments(
                    data_new_assignments,
                ),
            ),
        ],
    )

    new_assignments_study_semester = {
        "Status": [
            "Neue Zulassungen",
            "Neue Ablehnungen",
            "Neue Kombinationszulassungen",
            "Ausstehende Anmeldungen",
            "Insgesamt getätigte Selbstabmeldungen",
        ],
        "Ø Fachsemester": [
            round_mean_df_column(df_accepted_assignments, "fachsemester"),
            round_mean_df_column(df_denied_assignments, "fachsemester"),
            round_mean_df_column(
                df_accepted_lecture_combinations,
                "fachsemester",
            ),
            round_mean_df_column(
                df_assignments[
                    df_assignments["status"]
                    == consts.RULE_SETTING_STATUS_ENROLLED
                ],
                "fachsemester",
            ),
            round_mean_df_column(
                df_assignments[
                    df_assignments["status"]
                    == consts.RULE_SETTING_STATUS_SELF_DISENROLLED
                ],
                "fachsemester",
            ),
        ],
    }

    graph_mean_study_semester_per_status = html.Div(
        [
            html.H5("Ø Fachsemester pro Status", className=("mt-5")),
            dcc.Graph(
                figure=create_stat_tab_figure_mean_study_semester(
                    new_assignments_study_semester,
                ),
            ),
        ],
    )

    graph_assignment_status_per_rule = html.Div(
        [
            html.H5(
                "Anzahl neuer Belegungsstatus pro Regel", className=("mt-5")
            ),
            dcc.Graph(
                figure=layout_utils.create_barchart_for_rules(
                    df_all_new_assignments,
                    stat_info,
                ),
            ),
        ],
    )

    stat_tab = [
        overview,
        ruleset_name,
        ruleset_accordion,
        graph_new_assignments_per_status,
        graph_mean_study_semester_per_status,
        graph_assignment_status_per_rule,
    ]

    return stat_tab


def create_flex_piechart_figure(
    value_parameter: str,
    value_selector: str,
    df_accepted_assignments,
    df_denied_assignments,
    df_accepted_lecture_combinations,
    df_assignments,
    all_new_assignments,
    database_name,
):
    """Create a piechart figure based on input dropdowns and dataframes."""
    if value_parameter == "Anzahl Belegungen pro Status":
        column = "status"
    elif value_parameter == "Fachsemester":
        column = "fachsemester"
    elif value_parameter == "Studiengänge":
        column = "studiengangs_id"
    elif value_parameter == "Veranstaltungen":
        column = "veranstaltungs_id"
    elif value_parameter == "Gruppen":
        column = "gruppen_id"
    elif value_parameter == "Erstbelegungen":
        column = "erstbelegung"
    elif value_parameter == "Hörerstatus":
        column = "hoererstatus"
    elif value_parameter == "Studiumsart":
        column = "studiumsart"
    elif value_parameter == "Studiumstyp":
        column = "studiumstyp"

    if value_selector == "für neue Zulassungen und Ablehnungen":
        df = all_new_assignments
    elif value_selector == "für neue Zulassungen":
        df = df_accepted_assignments
    elif value_selector == "für neue Ablehnungen":
        df = df_denied_assignments
    elif value_selector == "für neue Kombinationseinschreibungen":
        df = df_accepted_lecture_combinations
    elif value_selector == "für ausstehende Anmeldungen":
        df = df_assignments[
            df_assignments["status"] == consts.RULE_SETTING_STATUS_ENROLLED
        ]
    elif value_selector == "für insgesamt getätigte Selbstabmeldungen":
        df = df_assignments[
            df_assignments["status"]
            == consts.RULE_SETTING_STATUS_SELF_DISENROLLED
        ]
    if value_selector == "für gesamtes Semester und Vorselektion":
        df = df_assignments

    if df.empty:
        # Show Empty piechart
        return px.pie(
            pd.DataFrame({"names": ["Keine Daten vorhanden"], "values": [1]}),
            names="names",
            values="values",
        )
    df = layout_utils.expand_db_value_names(df, column, database_name)

    flex_data = df[column].value_counts().reset_index()
    flex_data.columns = [column, "Anzahl"]
    flex_data = flex_data.sort_values(by=[column])

    figure = go.Figure(
        layout={"template": consts.VISU_SETTING_PLOTLY_THEME},
    )
    figure = px.pie(
        flex_data,
        values="Anzahl",
        names=column,
        template=consts.VISU_SETTING_PLOTLY_THEME,
        category_orders={column: flex_data[column].tolist()},
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    figure.update_traces(
        textposition="inside", hoverinfo="label+value", textinfo="label+value"
    )
    figure.update_layout(separators=".")

    return figure
