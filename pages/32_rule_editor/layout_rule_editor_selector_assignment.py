"""UI layout for value selection of assignment rules."""

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


rule_selector_assignment = html.Div(
    [
        html.H3("Belegungsregel:", className="mb-3"),
        dbc.Row(
            [
                # Rule naming
                dbc.Col(
                    html.P("Regelname: "),
                    width=1,
                ),
                dbc.Col(
                    dbc.Input(
                        id="input-assignment-name",
                        size="sm",
                    ),
                    width=9,
                ),
                # "Add" button
                dbc.Col(
                    dbc.Button(
                        [html.I(className="bi bi-plus-square")],
                        outline=False,
                        id="button-rule-editor-add-entry",
                    ),
                    width=1,
                    className="",
                ),
            ],
            className="mb-3",
        ),
        dbc.Row(
            [
                # Empty Col to create visual space
                dbc.Col(
                    width=1,
                ),
                # Left hand side table
                dbc.Col(
                    dbc.Select(
                        id="select-assignment-table-l",
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
                        id="select-assignment-column-l",
                        size="sm",
                    ),
                    width=2,
                ),
                # Operator
                dbc.Col(
                    dbc.Select(
                        id="select-assignment-operator",
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
                        id="select-assignment-table-r",
                        options=[
                            {"label": table, "value": table}
                            for table in dropdown_options_tables_r
                        ],
                        size="sm",
                        value=consts.STANDARD_NAME_FREE_INPUT,
                    ),
                    width=2,
                ),
                # Right hand side column selection with visible input field"
                # " type changed by table selection
                dbc.Col(
                    dbc.Select(
                        id="select-assignment-column-r",
                        size="sm",
                    ),
                    id="column-assignment-visibility-select",
                    width=2,
                ),
                dbc.Col(
                    [
                        dbc.Input(
                            id="input-assignment-column-r",
                            size="sm",
                        ),
                        dbc.Tooltip(
                            id="tooltip-assignment-column-r",
                            target="input-assignment-column-r",
                            placement="top",
                        ),
                    ],
                    id="column-assignment-visibility-input",
                    width=2,
                    style={"display": "none"},
                ),
            ],
            className="mb-3",
        ),
        # Additional rule row
        dbc.Row(
            [
                # logical_operation select
                dbc.Col(
                    dbc.Select(
                        id="select-assignment-logical-operation",
                        options=dropdown_options_logical_operation,
                        size="sm",
                    ),
                    width=1,
                ),
                # Left hand side table
                dbc.Col(
                    dbc.Select(
                        id="select-assignment-table-l2",
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
                        id="select-assignment-column-l2",
                        size="sm",
                    ),
                    width=2,
                ),
                # Operator
                dbc.Col(
                    dbc.Select(
                        id="select-assignment-operator2",
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
                        id="select-assignment-table-r2",
                        options=[
                            {"label": table, "value": table}
                            for table in dropdown_options_tables_r
                        ],
                        size="sm",
                        value=consts.STANDARD_NAME_FREE_INPUT,
                    ),
                    width=2,
                ),
                # Right hand side column selection with visible input field"
                # " type changed by table selection
                dbc.Col(
                    dbc.Select(
                        id="select-assignment-column-r2",
                        size="sm",
                    ),
                    id="column-assignment-visibility-select2",
                    width=2,
                ),
                dbc.Col(
                    [
                        dbc.Input(
                            id="input-assignment-column-r2",
                            size="sm",
                        ),
                        dbc.Tooltip(
                            id="tooltip-assignment-column-r2",
                            target="input-assignment-column-r2",
                            placement="top",
                        ),
                    ],
                    id="column-assignment-visibility-input2",
                    width=2,
                    style={"display": "none"},
                ),
            ],
        ),
        html.Hr(),
    ],
    className="mb-3",
)


# Selection menu of column left hand side - Row 1
@callback(
    Output("select-assignment-column-l", "options"),
    Input("select-assignment-table-l", "value"),
)
def update_select_assignment_column_l(value):
    """Add options to dropdown selector."""
    if value is not None:
        return [
            {"label": column, "value": column}
            for column in dropdown_options_tables_l[value]["columns"]
        ]
    return []


# Selection menu of column right hand side - Row 1
@callback(
    Output("select-assignment-column-r", "options"),
    Output("column-assignment-visibility-select", "style"),
    Output("column-assignment-visibility-input", "style"),
    Output("select-assignment-column-r", "value"),
    Output("input-assignment-column-r", "value"),
    Input("select-assignment-table-r", "value"),
)
def update_select_assignment_column_r(value):
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
                for column in dropdown_options_tables_r[value]["columns"]
            ],
            {},
            {"display": "none"},
            # Both Nones are used to clear the input field when switching
            # input types
            None,
            None,
        )
    return [], {"display": "none"}, {}, None, None


# Selection menu of column left hand side - Row 2
@callback(
    Output("select-assignment-column-l2", "options"),
    Input("select-assignment-table-l2", "value"),
)
def update_select_assignment_column_l2(value):
    """Add options to dropdown selector."""
    if value is not None:
        return [
            {"label": column, "value": column}
            for column in dropdown_options_tables_l[value]["columns"]
        ]
    return []


# Selection menu of column right hand side - Row 2
@callback(
    Output("select-assignment-column-r2", "options"),
    Output("column-assignment-visibility-select2", "style"),
    Output("column-assignment-visibility-input2", "style"),
    Output("select-assignment-column-r2", "value"),
    Output("input-assignment-column-r2", "value"),
    Input("select-assignment-table-r2", "value"),
)
def update_select_assignment_column_r2(value):
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
                for column in dropdown_options_tables_r[value]["columns"]
            ],
            {},
            {"display": "none"},
            None,
            None,
        )
    return [], {"display": "none"}, {}, None, None


@callback(
    Output("tooltip-assignment-column-r", "children"),
    Output("tooltip-assignment-column-r", "style"),
    Input("select-assignment-table-l", "value"),
    Input("select-assignment-column-l", "value"),
    Input("url-rule-editor", "search"),
)
def update_tooltip_possible_tooltip_r_values(
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

        # Sort alphabetically, but None should be last
        possible_values.sort(key=lambda x: (x is None, x))

        return str(possible_values).replace("'", ""), {}

    return "", {"display": "none"}


@callback(
    Output("tooltip-assignment-column-r2", "children"),
    Output("tooltip-assignment-column-r2", "style"),
    Input("select-assignment-table-l2", "value"),
    Input("select-assignment-column-l2", "value"),
    Input("url-rule-editor", "search"),
)
def update_tooltip_possible_tooltip_r2_values(
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

        return str(possible_values).replace("'", ""), {}

    return "", {"display": "none"}
