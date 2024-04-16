"""UI layout for value selection of preselection rules."""

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, html

import utils.constants as consts
from utils import db_utils, file_utils

base_db_structure = file_utils.read_json(
    consts.FOLDER_UTILS,
    consts.FILENAME_BASE_DB_STRUCTURE,
)

# Add selection option, used to select nothing
no_selection = {consts.EMPTY_STRING: {"columns": {consts.EMPTY_STRING: None}}}
# Used for free input
free_input = {
    consts.STANDARD_NAME_FREE_INPUT: {"columns": {consts.EMPTY_STRING: None}},
}

# Selection menu options
dropdown_options_tables_l = no_selection | base_db_structure.copy()
dropdown_options_tables_r = (
    no_selection | free_input | base_db_structure.copy()
)
dropdown_options_operators = no_selection | consts.OPERATORS.copy()
dropdown_options_logical_operation = [
    consts.EMPTY_STRING,
] + consts.JOIN_OPERATORS


rule_selector_preselection = html.Div(
    [
        html.H3("Vorselektion:", className="mb-3"),
        dbc.Row(
            [
                # Empty Col to create visual space
                dbc.Col(
                    width=1,
                ),
                # Left hand side table
                dbc.Col(
                    dbc.Select(
                        id="select-preselection-table-l",
                        options=[
                            {"label": table, "value": table}
                            for table in dropdown_options_tables_l
                        ],
                        size="sm",
                    ),
                    width=2,
                ),
                # Left hand side column
                dbc.Col(
                    dbc.Select(
                        id="select-preselection-column-l",
                        size="sm",
                    ),
                    width=2,
                ),
                # Operator
                dbc.Col(
                    dbc.Select(
                        id="select-preselection-operator",
                        options=[
                            {"label": operator, "value": operator}
                            for operator in dropdown_options_operators
                        ],
                        size="sm",
                    ),
                    width=1,
                ),
                # Right hand side table
                dbc.Col(
                    dbc.Select(
                        id="select-preselection-table-r",
                        options=[
                            {"label": table, "value": table}
                            for table in dropdown_options_tables_r
                        ],
                        size="sm",
                        value=consts.STANDARD_NAME_FREE_INPUT,
                    ),
                    width=2,
                ),
                # Right hand side column selection with visible input field
                # type changed by table selection
                dbc.Col(
                    dbc.Select(
                        id="select-preselection-column-r",
                        size="sm",
                    ),
                    id="column-preselection-visibility-select",
                    width=2,
                ),
                dbc.Col(
                    [
                        dbc.Input(
                            id="input-preselection-column-r",
                            size="sm",
                        ),
                        dbc.Tooltip(
                            id="tooltip-preselection-column-r",
                            target="input-preselection-column-r",
                            placement="top",
                        ),
                    ],
                    id="column-preselection-visibility-input",
                    width=2,
                    style={"display": "none"},
                ),
                # "Add" button
                dbc.Col(
                    dbc.Button(
                        [html.I(className="bi bi-check-square")],
                        outline=False,
                        id="button-preselection-add",
                    ),
                    width=1,
                    className="",
                ),
            ],
            className="mb-3",
        ),
        html.P(
            "Die Vorselektion kann genutzt werden, um zum Beispiel nur"
            " eine Veranstaltung oder einen Studiengang zu simulieren."
            f" Das aktuelle Semester '{consts.RULE_SETTING_CURRENT_SEMESTER}'"
            " muss hier nicht extra konfiguriert werden und kann in den"
            " Einstellungen auf der Startseite eingestellt werden.",
        ),
        html.Hr(),
    ],
    className="mb-3",
)


# Selection menu of column left hand side
@callback(
    Output("select-preselection-column-l", "options"),
    Input("select-preselection-table-l", "value"),
)
def update_select_preselection_column_l(value):
    """Add options to dropdown selector."""
    if value is not None:
        return [
            {"label": column, "value": column}
            for column in dropdown_options_tables_l[value]["columns"]
        ]
    return []


# Selection menu of column right hand side
@callback(
    Output("select-preselection-column-r", "options"),
    Output("column-preselection-visibility-select", "style"),
    Output("column-preselection-visibility-input", "style"),
    Output("select-preselection-column-r", "value"),
    Output("input-preselection-column-r", "value"),
    Input("select-preselection-table-r", "value"),
)
def update_select_preselection_column_r(value):
    """Add options to dropdown selector.

    Also switch input field types by changing visibility
    of dropdown and text input fields.
    Clears set values of right hand side when setting
    left hand side.
    """
    if value is not None and value != consts.STANDARD_NAME_FREE_INPUT:
        return (
            [
                {"label": column, "value": column}
                for column in dropdown_options_tables_r[value][
                    "columns"
                ]
            ],
            {},
            {"display": "none"},
            None,
            None,
        )
    return [], {"display": "none"}, {}, None, None


@callback(
    Output("tooltip-preselection-column-r", "children"),
    Output("tooltip-preselection-column-r", "style"),
    Input("select-preselection-table-l", "value"),
    Input("select-preselection-column-l", "value"),
    Input("url-rule-editor", "search"),
)
def update_tooltip_possible_tooltip_preselection_values(
    value_table,
    value_column,
    search,
):
    """Show tooltip with valid db values for input field."""
    if value_column and search:
        filename = file_utils.get_query_string(search, "filename")
        possible_values = db_utils.get_unique_column_values(
            filename,
            value_table,
            value_column,
        )

        if possible_values is None:
            return (
                "Zu viele Werte für Hinweisbox. Für mögliche Werte in der"
                " Datenbank nachschauen.",
                {},
            )

        possible_values.sort(key=lambda x: (x is None, x))
        return str(possible_values), {}

    return "", {"display": "none"}
