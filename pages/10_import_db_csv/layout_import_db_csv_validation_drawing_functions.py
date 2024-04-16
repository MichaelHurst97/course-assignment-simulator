"""UI layout for the validation of importing CSV files."""

from pathlib import Path

import dash_bootstrap_components as dbc
from dash import html


def create_alert(icon_type, icon_color, element_type, element_name, info_text):
    """Create dash bootstrap alert component with infos based on inputs."""
    return dbc.Alert(
        [
            html.I(className=f"bi {icon_type} me-2"),
            f"{element_type} '",
            html.B(element_name),
            f"' {info_text}",
        ],
        color=icon_color,
        className="d-flex align-items-center p-2",
    )


def draw_csv_file_presence_validation(import_csv_checked: dict):
    """Drawing definition to show available csv files."""
    children = []
    result = True

    for file, existing in import_csv_checked.items():
        # Remove file extension
        filename = Path(file).stem

        if existing:
            children.append(
                create_alert(
                    "bi-check-circle-fill",
                    "success",
                    "Datei",
                    filename,
                    "gefunden.",
                ),
            )

        elif existing is False:
            children.append(
                create_alert(
                    "bi-x-octagon-fill",
                    "danger",
                    "Datei",
                    filename,
                    "nicht gefunden.",
                ),
            )
            result = False

        else:
            raise TypeError

    return children, result


def draw_mapping_check_validation(import_mapping_checked: dict):
    """Drawing definition to show if import_mapping validates against
    base db structure.
    """
    children = []
    result = True

    for table, columns in import_mapping_checked.items():
        if not table:
            children.append(
                create_alert(
                    "bi-x-octagon-fill",
                    "danger",
                    "Tabelle",
                    table,
                    "kann nicht zugeordnet werden."
                    if table is False
                    # Show discard if table is None
                    else "wird verworfen.",
                ),
            )
            result = False
        elif not columns:
            children.append(
                create_alert(
                    "bi-exclamation-triangle-fill",
                    "warning",
                    "Tabelle",
                    table,
                    "wird von der Datenbank Struktur verlangt,"
                    " ist jedoch nicht im Mapping vorhanden."
                    if columns is None
                    else "ist im Mapping vorhanden, lässt sich jedoch"
                    " nicht der Basis Datenbank Struktur zuweisen.",
                ),
            )
            result = False
        else:
            children.append(
                create_alert(
                    "bi-check-circle-fill",
                    "success",
                    "Tabelle",
                    table,
                    "kann zugeordnet werden.",
                ),
            )

        if columns is not None and columns is not False:
            for column, existing in columns.items():
                if not existing:
                    children.append(
                        create_alert(
                            "bi-x-octagon-fill",
                            "danger"
                            if existing is False
                            else "bi-exclamation-triangle-fill",
                            "Spalte",
                            column,
                            "kann nicht zugeordnet werden."
                            if existing is False
                            else "wird von der Basis Datenbank Struktur"
                            " verlangt, ist aber nicht im Mapping vorhanden.",
                        ),
                    )
                    result = False
                else:
                    children.append(
                        create_alert(
                            "bi-check-circle-fill",
                            "success",
                            "Spalte",
                            column,
                            "kann zugeordnet werden.",
                        ),
                    )

    return children, result


def draw_import_mapping_validation(
    dtypes_checked: dict,
    map_to_columns_checked: dict,
):
    """Drawing definition to validate import_mapping against
    base db structure.
    """
    children = []
    result = True

    for table in dtypes_checked:
        for column_dtypes, value in dtypes_checked[table].items():
            if not value:
                children.append(
                    create_alert(
                        "bi-exclamation-triangle-fill",
                        "danger",
                        "Spalte",
                        column_dtypes,
                        "'dtypes' in JSON Datei stimmt nicht mit"
                        f" 'map_to_columns' überein: Spalte '{column_dtypes}'"
                        f" in Tabelle '{table}' kann nicht zu einer Spalte in"
                        " 'map_to_columns' zugeordnet werden.",
                    ),
                )
                result = False

    for table in map_to_columns_checked:
        for column, value in map_to_columns_checked[table].items():
            if not value:
                children.append(
                    create_alert(
                        "bi-exclamation-triangle-fill",
                        "danger",
                        "Spalte",
                        column,
                        "'map_to_columns' in JSON Datei stimmt nicht mit"
                        f" 'dtypes' überein: Spalte '{column}' in Tabelle"
                        f" '{table}' kann nicht zu einer Spalte in"
                        " 'dtypes' zugeordnet werden.",
                    ),
                )
                result = False

    if result:
        children.append(
            create_alert(
                "bi-check-circle-fill",
                "success",
                "Struktur der",
                "Mapping Datei",
                "ist korrekt.",
            ),
        )

    return children, result
