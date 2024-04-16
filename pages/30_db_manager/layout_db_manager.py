"""UI layout for managing and selecting database files."""

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, ctx, html

import utils.constants as consts
from utils import db_utils, file_utils

dash.register_page(
    __name__,
    path=consts.PAGE_DB_MANAGER_URL,
    title=consts.PAGE_DB_MANAGER_TITLE_NAME,
    name=consts.PAGE_DB_MANAGER_TITLE_NAME,
)


def get_db_info_for_folder():
    """Prepare db metainfo of all db files to be shown in ag-grid."""
    list_db = db_utils.get_db_filelist()

    # Use list for each db info element
    names = []
    ids = []
    rounds = []
    edit_dates = []
    creation_dates = []
    filesizes = []

    for db in list_db:
        info = db_utils.get_db_info(db)

        # Truncate string to not show .db file extension
        names.append(info["name"][:-3])
        ids.append(info["id"])
        rounds.append(info["runde"])
        # Truncate string to not show millisecs
        edit_dates.append(
            info["änderungs_datum"][:-7],
        )
        creation_dates.append(info["erstellungs_datum"][:-7])
        filesizes.append(info["filesize"])

    # Create df out of lists
    df = pd.DataFrame(
        {
            "Name": names,
            "ID": ids,
            "Runde": rounds,
            "Änderungsdatum": edit_dates,
            "Erstellungsdatum": creation_dates,
            "Dateigröße": filesizes,
        },
    )

    # Add checkbox to first column in table
    columnDefs = [
        {
            "field": column,
            # Checkbox for first column
            "checkboxSelection": True
            if df.columns.get_loc(column) == 0
            else False,
            # First column gets more space
            "flex": 2 if df.columns.get_loc(column) == 0 else 1,
        }
        for column in df.columns
    ]

    return df.to_dict("records"), columnDefs


page_heading = html.Div(
    [
        html.H2("Simulator & Datenbank-Manager"),
        html.P(
            "Zum Starten einer Simulation die importierten Belegungsdaten"
            " auswählen und auf weiter klicken.",
        ),
        html.Hr(),
    ],
)


grid = html.Div(
    [
        dag.AgGrid(
            id="ag-grid-dbm",
            className="ag-theme-alpine selection",
            dashGridOptions={
                "rowSelection": "single",
            },
            defaultColDef={"sortable": True},
            style={"height": "55vh", "width": "100%"},
            columnSize="sizeToFit",
        ),
    ],
)

grid_buttons = html.Div(
    [
        dbc.Button(
            [html.I(className="bi bi-trash me-2"), "Datenbank löschen"],
            outline=True,
            color="danger",
            class_name="mt-3",
            id="button-dbm-delete",
        ),
        dbc.Button(
            [html.I(className="bi bi-copy me-2"), "Datenbank duplizieren"],
            outline=True,
            color="secondary",
            class_name="mt-3 ms-3",
            id="button-dbm-duplicate",
            n_clicks=0,
        ),
        dbc.Button(
            [
                html.I(className="bi bi-pencil-square me-2"),
                "Datenbank umbennen",
            ],
            outline=True,
            color="secondary",
            class_name="mt-3 ms-3",
            id="button-dbm-rename",
            n_clicks=0,
        ),
        dbc.Button(
            [
                html.I(className="bi bi-arrow-clockwise me-2"),
                "Liste neu laden",
            ],
            outline=True,
            color="secondary",
            class_name="mt-3 ms-3",
            id="button-dbm-refresh",
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
                    href=consts.PAGE_HOME_URL,
                    outline=True,
                    color="primary",
                    className="me-auto",
                ),
                dbc.Button(
                    "Weiter",
                    color="primary",
                    className="ms-auto",
                    id="button-dbm-next",
                ),
            ],
            direction="horizontal",
            className="mb-5",
        ),
    ],
)

rename_modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Umbenennen")),
                dbc.ModalBody(
                    dbc.Input(
                        id="modal-dbm-rename-input",
                        placeholder="Neuer Name (ohne Dateiendung)...",
                        type="text",
                    ),
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "Abbrechen",
                            id="button-dbm-rename-deny",
                            outline=True,
                            className="ms-auto",
                            n_clicks=0,
                        ),
                        dbc.Button(
                            "Umbennen",
                            id="button-dbm-rename-accept",
                            className="me-0",
                            n_clicks=0,
                        ),
                    ],
                ),
            ],
            id="modal-dbm-rename",
            is_open=False,
        ),
    ],
)

delete_modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Löschen")),
                dbc.ModalBody(
                    [
                        html.P(
                            "Soll die ausgewählte Datenbank wirklich"
                            " gelöscht werden?",
                            id="modal-dbm-delete-text",
                        ),
                    ],
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "Abbrechen",
                            id="button-dbm-delete-deny",
                            color="primary",
                            outline=True,
                            className="ms-auto",
                            n_clicks=0,
                        ),
                        dbc.Button(
                            "Löschen",
                            id="button-dbm-delete-accept",
                            color="danger",
                            className="me-0",
                            n_clicks=0,
                        ),
                    ],
                ),
            ],
            id="modal-dbm-delete",
            is_open=False,
        ),
    ],
)

duplicate_modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Duplizieren")),
                dbc.ModalBody(
                    dbc.Input(
                        id="modal-dbm-duplicate-input",
                        placeholder="Neuer Name (ohne Dateiendung)...",
                        type="text",
                    ),
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "Abbrechen",
                            id="button-dbm-duplicate-deny",
                            outline=True,
                            className="ms-auto",
                            n_clicks=0,
                        ),
                        dbc.Button(
                            "Duplizieren",
                            id="button-dbm-duplicate-accept",
                            className="me-0",
                            n_clicks=0,
                        ),
                    ],
                ),
            ],
            id="modal-dbm-duplicate",
            is_open=False,
        ),
    ],
)

db_manager = html.Div(
    [
        page_heading,
        grid,
        grid_buttons,
        page_navigation,
        rename_modal,
        delete_modal,
        duplicate_modal,
    ],
    className="page-container",
)


layout = dbc.Container(db_manager, fluid=False, className="main-container")


@callback(
    Output("modal-dbm-delete", "is_open"),
    [
        Input("button-dbm-delete", "n_clicks"),
        Input("button-dbm-delete-deny", "n_clicks"),
        Input("button-dbm-delete-accept", "n_clicks"),
    ],
    [
        State("modal-dbm-delete", "is_open"),
        State("ag-grid-dbm", "selectedRows"),
    ],
)
def toggle_delete_modal(
    n_clicks,
    n_clicks_deny,
    n_clicks_accept,
    is_open,
    selectedRows,
):
    """Control opening / closing of delete action modal and it's deletion
    functionality.
    """
    triggered_id = ctx.triggered_id

    # Open modal only if row is selected
    if (
        (n_clicks and triggered_id == "button-dbm-delete" and selectedRows)
        or n_clicks_deny
        and triggered_id == "button-dbm-delete-deny"
    ):
        return not is_open

    # Accept deletion and close modal
    elif n_clicks_accept and triggered_id == "button-dbm-delete-accept":
        db_utils.delete_db(
            selectedRows[0][consts.AG_COLUMN_NAME_DBM_NAME] + ".db",
        )
        return not is_open

    # Close modal via x in top right modal corner
    return is_open


@callback(
    Output("modal-dbm-duplicate", "is_open"),
    [
        Input("button-dbm-duplicate", "n_clicks"),
        Input("button-dbm-duplicate-deny", "n_clicks"),
        Input("button-dbm-duplicate-accept", "n_clicks"),
    ],
    [
        State("modal-dbm-duplicate", "is_open"),
        State("modal-dbm-duplicate-input", "value"),
        State("ag-grid-dbm", "selectedRows"),
    ],
)
def toggle_duplicate_modal(
    n_clicks,
    n_clicks_deny,
    n_clicks_accept,
    is_open,
    value,
    selectedRows,
):
    """Control opening / closing of duplication action modal and it's
    duplication functionality.
    """
    triggered_id = ctx.triggered_id

    if (
        (n_clicks and triggered_id == "button-dbm-duplicate" and selectedRows)
        or n_clicks_deny
        and triggered_id == "button-dbm-duplicate-deny"
    ):
        value = None
        return not is_open

    elif (
        n_clicks_accept
        and triggered_id == "button-dbm-duplicate-accept"
        and value is not None
    ):
        value = file_utils.remove_invalid_input_field_characters(value)
        db_utils.duplicate_db(
            selectedRows[0][consts.AG_COLUMN_NAME_DBM_NAME] + ".db",
            value + ".db",
        )
        value = None
        return not is_open

    return is_open


@callback(
    Output("modal-dbm-rename", "is_open"),
    [
        Input("button-dbm-rename", "n_clicks"),
        Input("button-dbm-rename-deny", "n_clicks"),
        Input("button-dbm-rename-accept", "n_clicks"),
    ],
    [
        State("modal-dbm-rename", "is_open"),
        State("modal-dbm-rename-input", "value"),
        State("ag-grid-dbm", "selectedRows"),
    ],
)
def toggle_rename_modal(
    n_clicks,
    n_clicks_deny,
    n_clicks_accept,
    is_open,
    value,
    selectedRows,
):
    """Control opening / closing of rename action modal and it's renaming
    functionality.
    """
    triggered_id = ctx.triggered_id

    if (
        (n_clicks and triggered_id == "button-dbm-rename" and selectedRows)
        or n_clicks_deny
        and triggered_id == "button-dbm-rename-deny"
    ):
        value = None
        return not is_open

    elif (
        n_clicks_accept
        and triggered_id == "button-dbm-rename-accept"
        and value is not None
    ):
        value = file_utils.remove_invalid_input_field_characters(value)
        db_utils.rename_db(
            selectedRows[0][consts.AG_COLUMN_NAME_DBM_NAME] + ".db",
            value + ".db",
        )
        value = None
        return not is_open

    return is_open


@callback(
    Output("button-dbm-rename-accept", "disabled"),
    Input("modal-dbm-rename-input", "value"),
)
def check_renaming_allowed(value):
    """Enable rename button when renaming field is not empty."""
    if not value or value is None or str.isspace(value):
        return True
    return False


@callback(
    Output("button-dbm-duplicate-accept", "disabled"),
    Input("modal-dbm-duplicate-input", "value"),
)
def check_duplication_allowed(value):
    """Enable duplication button when duplication name field is not empty."""
    if not value or value is None or str.isspace(value):
        return True
    return False


@callback(
    Output("modal-dbm-duplicate-input", "value"),
    Input("button-dbm-duplicate", "n_clicks"),
    State("ag-grid-dbm", "selectedRows"),
)
def update_duplication_standard_filename(n_clicks, selectedRows):
    """Insert the currently selected row as filename into duplication input."""
    if n_clicks and selectedRows:
        return selectedRows[0][consts.AG_COLUMN_NAME_DBM_NAME] + " - Kopie"
    return None


@callback(
    Output("modal-dbm-rename-input", "value"),
    Input("button-dbm-rename", "n_clicks"),
    State("ag-grid-dbm", "selectedRows"),
)
def update_rename_standard_filename(n_clicks, selectedRows):
    """Insert the currently selected row as filename into rename input."""
    if n_clicks and selectedRows:
        return selectedRows[0][consts.AG_COLUMN_NAME_DBM_NAME]
    return None


@callback(
    Output("modal-dbm-delete-text", "children"),
    Input("button-dbm-delete", "n_clicks"),
    State("ag-grid-dbm", "selectedRows"),
)
def update_deletion_modal_filename(n_clicks, selectedRows):
    """Insert the currently selected row as filename into deletion message."""
    if n_clicks and selectedRows:
        return f"Soll die ausgewählte Datenbank '{selectedRows[0][consts.AG_COLUMN_NAME_DBM_NAME]}' wirklich gelöscht werden?"
    return None


@callback(
    [Output("ag-grid-dbm", "rowData"), Output("ag-grid-dbm", "columnDefs")],
    [
        Input("button-dbm-refresh", "n_clicks"),
        Input("modal-dbm-rename", "is_open"),
        Input("modal-dbm-delete", "is_open"),
        Input("modal-dbm-duplicate", "is_open"),
    ],
)
def update_table_entries(
    n_clicks,
    is_open_refresh,
    is_open_delete,
    is_open_duplicate,
):
    """Update ag-grid everytime the page loads, refresh button is pressed
    or modal opens or closes.
    """
    records, columnDefs = get_db_info_for_folder()
    return records, columnDefs


@callback(
    Output("button-dbm-next", "disabled"),
    Output("button-dbm-next", "href"),
    Input("ag-grid-dbm", "selectedRows"),
)
def toggle_next_button(selectedRows):
    """Enable the next page button when a row is selected."""
    if selectedRows is not None and selectedRows:
        return (
            False,
            f"{consts.PAGE_SIM_START_URL}?filename={selectedRows[0][consts.AG_COLUMN_NAME_DBM_NAME]}.db",
        )
    return True, ""
