"""Base UI layout for the validation of importing CSV files."""


import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, html

import utils.constants as consts
from utils import file_utils

from . import (
    layout_import_db_csv_validation_drawing_functions,
    model_import_db_csv_validation,
)

dash.register_page(
    __name__,
    path=consts.PAGE_IMPORT_DB_FILE_URL,
    title=consts.PAGE_IMPORT_DB_FILE_TITLE_NAME,
    name=consts.PAGE_IMPORT_DB_FILE_TITLE_NAME,
)

page_heading = html.Div(
    [
        html.H2("Abbild aus Datei importieren"),
        html.P(
            "Datenbank-Abbild als CSV Dateien im Ordner"
            f" '{consts.FOLDER_CSV_IMPORT}' platzieren."
            " Ein Mapping für die Zuweisung der Dateien an die interne"
            " Datenbankstruktur muss vorhanden sein.",
        ),
        html.Hr(),
    ],
)

internal_files_check = html.Div(
    [html.Div(id="div-import-validation-internal-files"), html.Hr()],
)

csv_files_check = html.Div(
    [
        html.H2("CSV Datei Überprüfung"),
        html.P("Existieren alle zu importierende CSV Dateien?"),
        html.Div(id="div-import-validation-csv-files"),
        html.Hr(),
    ],
)

mapping_structure_check = html.Div(
    [
        html.H2("Mapping Struktur Überprüfung"),
        html.P(
            "Stimmen die Werte innerhalb der Mapping Datei von Import nach"
            " Ziel-Datenbank?",
        ),
        html.Div(id="div-import-validation-mapping-structure"),
        html.Hr(),
    ],
)

mapping_check = html.Div(
    [
        html.H2("Mapping Überprüfung"),
        html.P(
            "Stimmt das angegebene Mapping mit der Basis Datenbank Struktur"
            " überein?",
        ),
        html.Div(id="div-import-validation-mapping"),
        html.Hr(),
    ],
)


button_refresh = html.Div(
    dbc.Button(
        [html.I(className="bi bi-arrow-clockwise me-2"), "Refresh"],
        outline=True,
        color="primary",
        className="mt-3",
        id="button-import-validation-refresh",
    ),
)

page_navigation = html.Div(
    [
        html.Hr(className="mt-5"),
        dbc.Stack(
            [
                dbc.Button(
                    "Zurück",
                    href=consts.PAGE_HOME_URL,
                    outline=True,
                    color="primary",
                    className="me-auto",
                ),
                dbc.Input(
                    placeholder="Name eingeben... Feld leer lassen für"
                    " automatische Namenswahl mit Datum",
                    type="text",
                    className="ms-auto",
                    id="input-import-validation-name",
                ),
                dbc.Button(
                    "Importieren",
                    color="primary",
                    className="ms-auto",
                    id="button-import-validation-next",
                ),
            ],
            direction="horizontal",
            gap=3,
            className="mb-5",
        ),
    ],
)

layout_import_db_csv_validation = html.Div(
    [
        page_heading,
        internal_files_check,
        csv_files_check,
        mapping_structure_check,
        mapping_check,
        button_refresh,
        page_navigation,
    ],
    className="page-container",
)

layout = dbc.Container(
    layout_import_db_csv_validation,
    fluid=False,
    className="main-container",
)


@callback(
    [
        Output("div-import-validation-internal-files", "children"),
        Output("div-import-validation-csv-files", "children"),
        Output("div-import-validation-mapping", "children"),
        Output("div-import-validation-mapping-structure", "children"),
        Output("button-import-validation-next", "disabled"),
    ],
    Input("button-import-validation-refresh", "n_clicks"),
)
def check_available_files(n_clicks):
    """Check and validate files, then draw the result as children of various
    html elements.

    All validations must be done in this function output the result to the
    disable button parameter. Only one Output should exist for a callback.
    """

    children_interal_files = []

    # Draw message if mapping is found
    import_mapping = file_utils.read_json(
        consts.FOLDER_CSV_IMPORT,
        consts.FILENAME_IMPORT_MAPPING,
    )
    if import_mapping is not None:
        message = dbc.Alert(
            [
                html.I(className="bi bi-check-circle-fill me-2"),
                f"Datei für Import Mapping ({consts.FILENAME_IMPORT_MAPPING})"
                " im Import-Ordner gefunden.",
            ],
            color="success",
            className="d-flex align-items-center",
        )
        children_interal_files.append(message)
    # Error reporting for missing mapping
    if import_mapping is None:
        message = dbc.Alert(
            [
                html.I(className="bi bi-exclamation-triangle-fill me-2"),
                f"Datei für Import Mapping ({consts.FILENAME_IMPORT_MAPPING})"
                " nicht im Import-Ordner gefunden.",
            ],
            color="danger",
            className="d-flex align-items-center",
        )
        disable_next_button = True
        children_interal_files.append(message)

    # Draw message if db structure is found
    base_db_structure = file_utils.read_json(
        consts.FOLDER_UTILS,
        consts.FILENAME_BASE_DB_STRUCTURE,
    )
    if base_db_structure is not None:
        message = dbc.Alert(
            [
                html.I(className="bi bi-check-circle-fill me-2"),
                "Datei für Datenbank Struktur"
                f" ({consts.FILENAME_BASE_DB_STRUCTURE}) im"
                " utils Ordner gefunden.",
            ],
            color="success",
            className="d-flex align-items-center",
        )
        children_interal_files.append(message)
    # Error reporting for missing db structure
    if base_db_structure is None:
        message = dbc.Alert(
            [
                html.I(className="bi bi-exclamation-triangle-fill me-2"),
                "Datei für Datenbank Struktur"
                f" ({consts.FILENAME_BASE_DB_STRUCTURE}) nicht im utils"
                " Ordner gefunden. Datei-Integrität des Projekts"
                " überprüfen und ggf. Projekt neu installieren",
            ],
            color="danger",
            className="d-flex align-items-center",
        )
        disable_next_button = True
        children_interal_files.append(message)

    # Drawing of each csv item that was checked
    if import_mapping is not None and base_db_structure is not None:
        import_csvs_checked = (
            model_import_db_csv_validation.check_csv_presence(
                consts.FOLDER_CSV_IMPORT,
                import_mapping,
            )
        )
        import_mapping_checked = (
            model_import_db_csv_validation.check_mapping_against_db_structure(
                import_mapping,
                base_db_structure,
            )
        )
        (
            dtypes_checked,
            map_columns_checked,
        ) = model_import_db_csv_validation.verify_mapping_structure(
            import_mapping,
        )

        (
            children_csv,
            result_csv,
        ) = layout_import_db_csv_validation_drawing_functions.draw_csv_file_presence_validation(
            import_csvs_checked,
        )
        (
            children_mapping,
            result_mapping,
        ) = layout_import_db_csv_validation_drawing_functions.draw_mapping_check_validation(
            import_mapping_checked,
        )
        (
            children_mapping_structure,
            mapping_structure,
        ) = layout_import_db_csv_validation_drawing_functions.draw_import_mapping_validation(
            dtypes_checked,
            map_columns_checked,
        )

        # Missing files disable the next button
        disable_next_button = True
        if result_csv or result_mapping or mapping_structure:
            disable_next_button = False

    # Return as html children
    return (
        children_interal_files,
        children_csv,
        children_mapping,
        children_mapping_structure,
        disable_next_button,
    )


@callback(
    Output("button-import-validation-next", "href"),
    Input("input-import-validation-name", "value"),
)
def update_next_button_query_string(value):
    """Set input filename or default value as href of next button."""
    if not value or value is None or str.isspace(value):
        return f"{consts.PAGE_IMPORT_DB_FILE_PROCESS_URL}?filename=default"

    value = file_utils.remove_invalid_input_field_characters(value)
    return f"{consts.PAGE_IMPORT_DB_FILE_PROCESS_URL}?filename={value}.db"
