"""Base UI layout to create and edit rulesets."""

from pathlib import Path

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import (
    Input,
    Output,
    Patch,
    State,
    callback,
    ctx,
    dcc,
    html,
    no_update,
)

import utils.constants as consts
from utils import file_utils, layout_utils, rule_utils
from utils.logger import logger

from . import (
    layout_rule_editor_selector_assignment,
    layout_rule_editor_selector_preselection,
)


def check_string_to_int(input):
    """Cast a string to int if only digits."""
    if isinstance(input, int):
        return input
    elif isinstance(input, str) and input.isdigit():
        return int(input)
    else:
        return input


def save_current_grid_ruleset(
    virtualRowData: list,
    filename: str,
    rule_preselection: list,
):
    """Serialize grid data as json file.

    VirtualRowData represents the current grid rows in order.
    """
    if virtualRowData:
        # Preselection
        dict_rule_preselection = {}
        if rule_preselection:
            rule_preselection = rule_preselection[0]
            
            if "Tabelle L" in rule_preselection:
                dict_rule_preselection = {
                    "table_x": rule_preselection["Tabelle L"],
                    "column_x": rule_preselection["Spalte L"],
                    "operator_symbol": rule_preselection["Operator"],
                    "table_y": rule_preselection["Tabelle R"]
                    if rule_preselection["Tabelle R"] != "Freie Eingabe"
                    else None,
                    "column_y": check_string_to_int(rule_preselection["Spalte R"]),
                }

        # Assignment rules
        list_rules_assignment = []
        for rule_assignment in virtualRowData:
            if "Log Op" in rule_assignment:
                dict_rule_assignment = {
                    "rule_name": rule_assignment["Name"],
                    "rule_assignment": {
                        "table_x": rule_assignment["Tabelle L"],
                        "column_x": rule_assignment["Spalte L"],
                        "operator_symbol": rule_assignment["Operator"],
                        "table_y": rule_assignment["Tabelle R"]
                        if rule_assignment["Tabelle R"] != "Freie Eingabe"
                        else None,
                        "column_y": check_string_to_int(rule_assignment["Spalte R"]),
                    },
                    "rule_join_operation": rule_assignment["Log Op"],
                    "rule_assignment_2": {
                        "table_x": rule_assignment["Tabelle L2"],
                        "column_x": rule_assignment["Spalte L2"],
                        "operator_symbol": rule_assignment["Operator2"],
                        "table_y": rule_assignment["Tabelle R2"]
                        if rule_assignment["Tabelle R2"] != "Freie Eingabe"
                        else None,
                        "column_y": check_string_to_int(rule_assignment["Spalte R2"]),
                    },
                }

            else:
                dict_rule_assignment = {
                    "rule_name": rule_assignment["Name"],
                    "rule_assignment": {
                        "table_x": rule_assignment["Tabelle L"],
                        "column_x": rule_assignment["Spalte L"],
                        "operator_symbol": rule_assignment["Operator"],
                        "table_y": rule_assignment["Tabelle R"]
                        if rule_assignment["Tabelle R"] != "Freie Eingabe"
                        else None,
                        "column_y": check_string_to_int(rule_assignment["Spalte R"]),
                    },
                    "rule_join_operation": None,
                    "rule_assignment_2": None,
                }

            list_rules_assignment.append(dict_rule_assignment)

        rule_set = {
            "rule_preselection": dict_rule_preselection,
            "rules_assignment": list_rules_assignment,
        }

        file_utils.write_json(
            rule_set,
            file_utils.get_folder(consts.FOLDER_RULE_FILES),
            filename + ".json",
        )

        logger.info(f"Regel-Datei '{filename + ".json"}' geschrieben")


dash.register_page(
    __name__,
    path=consts.PAGE_SIM_RULE_EDITOR_URL,
    title=consts.PAGE_SIM_RULE_EDITOR_TITLE_NAME,
    name=consts.PAGE_SIM_RULE_EDITOR_TITLE_NAME,
)


page_heading = html.Div(
    [
        html.H2("Schritt 2: Regeleditor"),
        html.P(
            "Hier kann eine Liste an Regeln zur Belegungspriorität selbst"
            " gestaltet werden. Die Regeln werden nacheinander abgearbeitet"
            " und entfernen damit eine Schnittmenge der Belegwünsche.",
        ),
        html.Hr(),
    ],
)

# Ag-Grid column definition
columnDefs = [
    {
        "field": "Nr",
        "rowDrag": True,
        "checkboxSelection": True,
        "width": 70,
    },
    {
        "field": "Name",
        "width": 200,
    },
    {
        "field": "Tabelle L",
        "width": 120,
    },
    {
        "field": "Spalte L",
        "width": 120,
    },
    {
        "field": "Operator",
        "width": 100,
    },
    {
        "field": "Tabelle R",
        "width": 120,
    },
    {
        "field": "Spalte R",
        "width": 120,
    },
    {
        "field": "Log Op",
        "width": 100,
    },
    {
        "field": "Tabelle L2",
        "width": 120,
    },
    {
        "field": "Spalte L2",
        "width": 120,
    },
    {
        "field": "Operator2",
        "width": 100,
    },
    {
        "field": "Tabelle R2",
        "width": 120,
    },
    {
        "field": "Spalte R2",
        "width": 120,
    },
]
grid = dag.AgGrid(
    id="grid-rule-editor",
    className="ag-theme-alpine selection",
    columnDefs=columnDefs,
    rowData=[],
    dashGridOptions={
        "rowDragManaged": True,
        "animate": True,
        "pinnedTopRowData": [{"Nr": 0, "Name": "Vorselektion"}],
    },
    defaultColDef={
        "sortable": False,
        "suppressMovable": True,
        "resizable": True,
    },
    style={"height": "50vh", "width": "100%"},
    getRowId="params.data.Nr",
)

grid_buttons = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Button(
                            [
                                html.I(className="bi bi-trash me-2"),
                                "Regeleintrag löschen",
                            ],
                            outline=True,
                            color="danger",
                            className="mt-3",
                            id="button-rule-editor-remove-entry",
                        ),
                    ],
                    width=10,
                ),
                dbc.Col(
                    [
                        dbc.Button(
                            [
                                html.I(className="bi bi-upload me-2"),
                                "Regelset laden",
                            ],
                            outline=True,
                            color="secondary",
                            className="mt-3",
                            id="button-rule-editor-load-ruleset",
                        ),
                    ],
                    width=2,
                    className="d-flex justify-content-end",
                ),
            ],
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
                    id="button-rule-editor-back",
                ),
                dbc.Button(
                    "Speichern & Weiter",
                    color="primary",
                    className="ms-auto",
                    id="button-rule-editor-next",
                ),
            ],
            direction="horizontal",
            className="mb-5",
        ),
    ],
)

save_ruleset_modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Speichern")),
                dbc.ModalBody(
                    dbc.Input(
                        id="modal-rule-editor-save-input",
                        placeholder="Name (ohne Dateiendung)...",
                        type="text",
                    ),
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "Abbrechen",
                            id="button-rule-editor-save-deny",
                            outline=True,
                            className="ms-auto",
                            n_clicks=0,
                        ),
                        dbc.Button(
                            "Speichern & Weiter",
                            id="button-rule-editor-save-accept",
                            className="me-0",
                            n_clicks=0,
                        ),
                    ],
                ),
            ],
            id="modal-rule-editor-save",
            is_open=False,
        ),
    ],
)

load_ruleset_modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Regelset laden")),
                dbc.ModalBody(
                    dag.AgGrid(
                        id="grid-rule-editor-load-ruleset",
                        className="ag-theme-alpine selection",
                        columnDefs=[
                            {
                                "field": "Dateiname",
                                "checkboxSelection": True,
                            },
                        ],
                        dashGridOptions={
                            "rowSelection": "single",
                        },
                        defaultColDef={"sortable": True},
                        columnSize="sizeToFit",
                        style={"height": "50vh", "width": "100%"},
                    ),
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "Abbrechen",
                            id="button-rule-editor-load-deny",
                            outline=True,
                            className="ms-auto",
                            n_clicks=0,
                        ),
                        dbc.Button(
                            "Laden",
                            id="button-rule-editor-load-accept",
                            className="me-0",
                            n_clicks=0,
                        ),
                    ],
                ),
            ],
            size="xl",
            id="modal-rule-editor-load",
            is_open=False,
        ),
    ],
)


rule_editor = html.Div(
    [
        dcc.Location(id="url-rule-editor"),
        dcc.Store(id="store-rule-editor"),
        page_heading,
        layout_rule_editor_selector_preselection.rule_selector_preselection,
        layout_rule_editor_selector_assignment.rule_selector_assignment,
        grid,
        grid_buttons,
        save_ruleset_modal,
        load_ruleset_modal,
        page_navigation,
    ],
    className="page-container",
)

layout = dbc.Container(rule_editor, fluid=False, className="main-container")


# Loading preselection values into grid - done in this file for easy access to
# global preselection variable
@callback(
    Output("grid-rule-editor", "dashGridOptions"),
    Output("store-rule-editor", "data"),
    Input("button-preselection-add", "n_clicks"),
    Input("button-rule-editor-load-accept", "n_clicks"),
    Input("grid-rule-editor-load-ruleset", "selectedRows"),
    State("store-rule-editor", "data"),
    Input("select-preselection-table-l", "value"),
    Input("select-preselection-column-l", "value"),
    Input("select-preselection-operator", "value"),
    Input("select-preselection-table-r", "value"),
    Input("select-preselection-column-r", "value"),
    Input("input-preselection-column-r", "value"),
)
def update_grid_preselection(
    n_clicks,
    n_clicks_load,
    selectedRows,
    data_store,
    table_l,
    column_l,
    op,
    table_r,
    column_select_r,
    column_input_r,
):
    """Update the preselection rule in grid via user selection or when loading
    ruleset file.
    """
    # Add from UI
    if ctx.triggered_id == "button-preselection-add":
        # Check if one of the two input types (select vs free input) is
        # active/None
        if column_input_r is None and layout_utils.validate_input_field_values(
            table_l,
            column_l,
            op,
            table_r,
            column_select_r,
        ):
            rule_preselection = [
                {
                    "Nr": "0",
                    "Name": "Vorselektion",
                    "Tabelle L": table_l,
                    "Spalte L": column_l,
                    "Operator": op,
                    "Tabelle R": table_r,
                    "Spalte R": column_select_r,
                },
            ]
        elif (
            column_select_r is None
            and layout_utils.validate_input_field_values(
                table_l,
                column_l,
                op,
                table_r,
                column_input_r,
            )
        ):
            rule_preselection = [
                {
                    "Nr": "0",
                    "Name": "Vorselektion",
                    "Tabelle L": table_l,
                    "Spalte L": column_l,
                    "Operator": op,
                    "Tabelle R": table_r,
                    "Spalte R": column_input_r,
                },
            ]

        else:
            rule_preselection = [{"Nr": "0", "Name": "Vorselektion"}]

        data_store = data_store or {}
        data_store["rule_preselection"] = rule_preselection

        grid_option_patch = Patch()
        grid_option_patch["pinnedTopRowData"] = rule_preselection
        return grid_option_patch, data_store

    # Load from file
    elif (
        selectedRows
        and n_clicks_load
        and ctx.triggered_id == "button-rule-editor-load-accept"
    ):
        ruleset = selectedRows[0]["Dateiname"]

        rule_preselection, _ = rule_utils.read_rule_file(
            consts.FOLDER_RULE_FILES,
            ruleset,
        )

        if rule_preselection:
            
            if rule_preselection.table_y is None:
                table_y = "Freie Eingabe"
            else:
                table_y = rule_preselection.table_y 
            
            rule_preselection = [
                {
                    "Nr": "0",
                    "Name": "Vorselektion",
                    "Tabelle L": rule_preselection.table_x,
                    "Spalte L": rule_preselection.column_x,
                    "Operator": rule_preselection.operator_symbol,
                    "Tabelle R": table_y,
                    "Spalte R": rule_preselection.column_y,
                },
            ]
        else:
            rule_preselection = [{"Nr": "0", "Name": "Vorselektion"}]

        data_store = data_store or {}
        data_store["rule_preselection"] = rule_preselection

        grid_option_patch = Patch()
        grid_option_patch["pinnedTopRowData"] = rule_preselection
        return grid_option_patch, data_store

    return {}, data_store


# Loading assignment selection values into grid
@callback(
    Output("grid-rule-editor", "rowTransaction"),
    Input("button-rule-editor-add-entry", "n_clicks"),
    Input("button-rule-editor-remove-entry", "n_clicks"),
    Input("input-assignment-name", "value"),
    Input("select-assignment-table-l", "value"),
    Input("select-assignment-column-l", "value"),
    Input("select-assignment-operator", "value"),
    Input("select-assignment-table-r", "value"),
    Input("select-assignment-column-r", "value"),
    Input("input-assignment-column-r", "value"),
    Input("select-assignment-logical-operation", "value"),
    Input("select-assignment-table-l2", "value"),
    Input("select-assignment-column-l2", "value"),
    Input("select-assignment-operator2", "value"),
    Input("select-assignment-table-r2", "value"),
    Input("select-assignment-column-r2", "value"),
    Input("input-assignment-column-r2", "value"),
    State("grid-rule-editor", "selectedRows"),
)
def update_grid_assignment_rules(
    n_clicks_add,
    n_clicks_remove,
    name,
    table_l,
    column_l,
    op,
    table_r,
    column_select_r,
    column_input_r,
    logical_operation,
    table_l2,
    column_l2,
    op2,
    table_r2,
    column_select_r2,
    column_input_r2,
    selectedRows,
):
    """Row transactions to remove and add rows to grid based on assignment rule
    selection input.
    """
    # Remove rows
    if selectedRows:
        if (
            n_clicks_remove
            and ctx.triggered_id == "button-rule-editor-remove-entry"
        ):
            return {"remove": selectedRows}

    # Add rows
    if n_clicks_add and ctx.triggered_id == "button-rule-editor-add-entry":
        # Check if one of the two input types (select vs free input) is
        # active/None
        first_row = False
        second_row = False
        if column_input_r is None and layout_utils.validate_input_field_values(
            name,
            table_l,
            column_l,
            op,
            table_r,
            column_select_r,
        ):
            first_row = {
                "Name": name,
                "Tabelle L": table_l,
                "Spalte L": column_l,
                "Operator": op,
                "Tabelle R": table_r,
                "Spalte R": column_select_r,
            }

        elif (
            column_select_r is None
            and layout_utils.validate_input_field_values(
                name,
                table_l,
                column_l,
                op,
                table_r,
                column_input_r,
            )
        ):
            first_row = {
                "Name": name,
                "Tabelle L": table_l,
                "Spalte L": column_l,
                "Operator": op,
                "Tabelle R": table_r,
                "Spalte R": column_input_r,
            }

        if (
            column_input_r2 is None
            and layout_utils.validate_input_field_values(
                logical_operation,
                table_l2,
                column_l2,
                op2,
                table_r2,
                column_select_r2,
            )
        ):
            second_row = {
                "Log Op": logical_operation,
                "Tabelle L2": table_l2,
                "Spalte L2": column_l2,
                "Operator2": op2,
                "Tabelle R2": table_r2,
                "Spalte R2": column_select_r2,
            }

        elif (
            column_select_r is None
            and layout_utils.validate_input_field_values(
                logical_operation,
                table_l2,
                column_l2,
                op2,
                table_r2,
                column_input_r2,
            )
        ):
            second_row = {
                "Log Op": logical_operation,
                "Tabelle L2": table_l2,
                "Spalte L2": column_l2,
                "Operator2": op2,
                "Tabelle R2": table_r2,
                "Spalte R2": column_input_r2,
            }

        if first_row and not second_row:
            # Set id to a high number so id's dont collide when loaded data
            # from rulset is already present
            rule_assignment = {
                "Nr": str(n_clicks_add + 1000 or 1000),
                **first_row,
            }
            return {"add": [rule_assignment]}

        elif first_row and second_row:
            rule_assignment = {
                "Nr": str(n_clicks_add + 1000 or 1000),
                **first_row,
                **second_row,
            }
            return {"add": [rule_assignment]}

        else:
            return no_update

    else:
        return no_update


@callback(
    Output("button-rule-editor-load-accept", "disabled"),
    Input("grid-rule-editor-load-ruleset", "selectedRows"),
)
def update_load_modal_accept_button_href(selectedRows):
    """Enable load rulset button if a ruleset is selected."""
    if selectedRows:
        return False
    return True


@callback(
    Output("grid-rule-editor", "rowData"),
    Output("store-rule-editor", "data", allow_duplicate=True),
    Input("button-rule-editor-load-accept", "n_clicks"),
    Input("grid-rule-editor-load-ruleset", "selectedRows"),
    Input("store-rule-editor", "data"),
    prevent_initial_call=True,
)
def load_grid_assignment_rules(n_clicks_load, selectedRows, data_store):
    """Populate the grid with ruleset file data."""
    if (
        selectedRows
        and n_clicks_load
        and ctx.triggered_id == "button-rule-editor-load-accept"
    ):
        ruleset = selectedRows[0]["Dateiname"]

        _, list_rule_assignments = rule_utils.read_rule_file(
            consts.FOLDER_RULE_FILES,
            ruleset,
        )

        list_rule_assignments_unpacked = []
        count = 1

        for rule_assignment in list_rule_assignments:
            rule = rule_assignment["rule_assignment"]
            op = rule_assignment["rule_join_operation"]
            rule2 = rule_assignment["rule_assignment_2"]

            if op is None and rule2 is None:
                if rule.table_y is None:
                    table_r = "Freie Eingabe"
                else:
                    table_r = rule.table_y

                rule_assignment = {
                    "Nr": str(count),
                    "Name": rule_assignment["rule_name"],
                    "Tabelle L": rule.table_x,
                    "Spalte L": rule.column_x,
                    "Operator": rule.operator_symbol,
                    "Tabelle R": table_r,
                    "Spalte R": rule.column_y,
                }

                count += 1
                list_rule_assignments_unpacked.append(rule_assignment)

            else:
                if rule.table_y is None:
                    table_r = "Freie Eingabe"
                else:
                    table_r = rule.table_y

                if rule2.table_y is None:
                    table_r2 = "Freie Eingabe"
                else:
                    table_r2 = rule2.table_y

                rule_assignment = {
                    "Nr": str(count),
                    "Name": rule_assignment["rule_name"],
                    "Tabelle L": rule.table_x,
                    "Spalte L": rule.column_x,
                    "Operator": rule.operator_symbol,
                    "Tabelle R": table_r,
                    "Spalte R": rule.column_y,
                    "Log Op": op,
                    "Tabelle L2": rule2.table_x,
                    "Spalte L2": rule2.column_x,
                    "Operator2": rule2.operator_symbol,
                    "Tabelle R2": table_r2,
                    "Spalte R2": rule2.column_y,
                }

                count += 1
                list_rule_assignments_unpacked.append(rule_assignment)

        if not data_store:
            data_store = {"ruleset": ruleset}
        else:
            data_store["ruleset"] = ruleset

        return list_rule_assignments_unpacked, data_store

    else:
        return no_update, no_update


@callback(
    Output("modal-rule-editor-load", "is_open"),
    [
        Input("button-rule-editor-load-ruleset", "n_clicks"),
        Input("button-rule-editor-load-deny", "n_clicks"),
        Input("button-rule-editor-load-accept", "n_clicks"),
    ],
    [
        State("modal-rule-editor-load", "is_open"),
        State("grid-rule-editor-load-ruleset", "selectedRows"),
    ],
)
def toggle_load_modal(
    n_clicks,
    n_clicks_deny,
    n_clicks_accept,
    is_open,
    selectedRows,
):
    """Toggle load ruleset modal."""
    triggered_id = ctx.triggered_id

    if (
        n_clicks_deny
        and triggered_id == "button-rule-editor-load-deny"
        or (
            n_clicks_accept
            and triggered_id == "button-rule-editor-load-accept"
            and selectedRows
        )
        or (n_clicks and triggered_id == "button-rule-editor-load-ruleset")
    ):
        return not is_open

    return is_open


@callback(
    Output("grid-rule-editor-load-ruleset", "rowData"),
    Input("modal-rule-editor-load", "is_open"),
)
def get_load_modal_ruleset_filelist(is_open):
    """Get ruleset filelist from filesystem."""
    files = rule_utils.get_ruleset_filelist()

    output = []

    for file in files:
        row = {
            "Dateiname": file,
        }
        output.append(row)

    return output


@callback(
    Output("modal-rule-editor-save", "is_open"),
    [
        Input("button-rule-editor-next", "n_clicks"),
        Input("button-rule-editor-save-deny", "n_clicks"),
        Input("button-rule-editor-save-accept", "n_clicks"),
    ],
    [
        State("modal-rule-editor-save", "is_open"),
        State("modal-rule-editor-save-input", "value"),
        State("grid-rule-editor", "virtualRowData"),
        State("store-rule-editor", "data"),
    ],
)
def toggle_save_modal(
    n_clicks,
    n_clicks_deny,
    n_clicks_accept,
    is_open,
    value,
    virtualRowData,
    data_store,
):
    """Toggle save modal on button clicks.
    Save rulset when save button is clicked before closing.
    """
    triggered_id = ctx.triggered_id
    if (
        n_clicks
        and triggered_id == "button-rule-editor-next"
        and virtualRowData
    ) or (n_clicks_deny and triggered_id == "button-rule-editor-save-deny"):
        value = None
        return not is_open

    # Save ruleset to file and continue
    elif (
        n_clicks_accept
        and triggered_id == "button-rule-editor-save-accept"
        and value is not None
    ):
        value = file_utils.remove_invalid_input_field_characters(value)
        
        if data_store is not None:
            save_current_grid_ruleset(
                virtualRowData, value, data_store["rule_preselection"],
            )
        else:
            save_current_grid_ruleset(
                virtualRowData, value, None,
            )
        return not is_open

    return is_open


@callback(
    Output("button-rule-editor-save-accept", "disabled"),
    Output("button-rule-editor-save-accept", "href"),
    Input("modal-rule-editor-save-input", "value"),
    Input("url-rule-editor", "search"),
)
def set_save_modal_accept_href(value, search):
    """Add href to next button, containing ruleset and db file query string."""
    if search and value or value is not None:
        filename = file_utils.get_query_string(search, "filename")
        return (
            False,
            f"{consts.PAGE_SIM_PROCESS_URL}?filename={filename}&ruleset={value + ".json"}",
        )

    return True, "/"


@callback(
    Output("modal-rule-editor-save-input", "value"),
    Input("button-rule-editor-next", "n_clicks"),
    State("store-rule-editor", "data"),
)
def update_save_modal_standard_filename(n_clicks, data_store):
    """Add standard filename to modal input field when ruleset was already
    loaded.
    """
    if n_clicks and data_store is not None:
        return Path(data_store["ruleset"]).stem
    return None


@callback(
    Output("button-rule-editor-next", "disabled"),
    Input("grid-rule-editor", "virtualRowData"),
)
def toggle_next_button(virtualRowData):
    """Toggle next button if grid has at least one row."""
    if not virtualRowData:
        return True
    return False


@callback(
    Output("button-rule-editor-back", "href"),
    Input("url-rule-editor", "search"),
)
def update_href_back_button(search):
    """Set back button href to current query string."""
    return f"{consts.PAGE_SIM_START_URL}{search}"


@callback(
    Output("url-rule-editor", "href"),
    Input("url-rule-editor", "search"),
    Input("url-rule-editor", "pathname"),
)
def redirect_when_missing_query_string(search, pathname):
    """Redirect to home page if query string is missing."""
    if (
        not search
        and not file_utils.get_query_string(search, "filename")
        and pathname != consts.PAGE_SIM_RULE_EDITOR_URL
        and pathname != consts.PAGE_SIM_PROCESS_URL
    ):
        logger.error(
            "Keine Datenbank Angabe im Query String gefunden!"
            " Bitte dem Programmablauf folgen und ab dem Datenbank Manager"
            " starten",
        )
        return consts.PAGE_HOME_URL
