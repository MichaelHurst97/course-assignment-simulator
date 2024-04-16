"""UI layout for some assignment modification utilities.

The variable name 'target' in this file always describes the table on which
a modification should be made. Either a lecture or a study program.
"""

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, ctx, dcc, html

import utils.constants as consts
from utils import db_utils

from . import (
    model_generate_new_assignments,
    model_reset_assignment_status,
    model_trigger_self_disenrollment,
)


def validate_and_cast_int(value, value_default):
    """Validate if input field is not empty, then cast to int.

    Input field type is string, so a check is also needed to see if
    input only consists of empty strings.
    """
    if value and isinstance(value, str) and not str.isspace(value):
        return int(value)
    return value_default


dash.register_page(
    __name__,
    path=consts.PAGE_GENERATOR_URL,
    title=consts.PAGE_GENERATOR_TITLE_NAME,
    name=consts.PAGE_GENERATOR_TITLE_NAME,
)

loading_generator_fullscreen = html.Div(
    dbc.Spinner(
        html.Div(id="spinner-modify-assignments-fullscreen"),
        fullscreen=True,
    ),
)

input_target_id = dbc.Stack(
    [
        html.Div(
            html.H3(
                "Veranstaltungs- / Studiengangs-ID: ",
                className="text-center",
            ),
        ),
        html.Div(
            dbc.Select(
                options=["", "veranstaltungs_id", "studiengangs_id"],
                id="select-modify-assignments-target-type",
            ),
        ),
        html.Div(
            # Most imports have too many lectures (HTW dataset has 22590)
            # so use text input instead of dropdown
            dbc.Input(
                id="input-modify-assignments-set-target",
            ),
        ),
        dbc.Tooltip(
            "Muss ein numerischer Wert sein. Für eine Liste an verfügbaren"
            " Veranstaltungen bitte in der jeweiligen SQLite Datenbank"
            " nachschauen.",
            target="input-modify-assignments-set-target",
            placement="top",
        ),
        html.Div(
            dbc.Button(
                "Einstellung ausstehend",
                outline=True,
                color="primary",
                id="button-modify-assignments-generator-set-target",
                n_clicks=0,
            ),
        ),
    ],
    direction="horizontal",
    gap=3,
    className="mt-3",
)

input_database = dbc.Stack(
    [
        html.Div(
            html.H3("Datenbank: ", className="text-center"),
        ),
        html.Div(dbc.Select(id="select-modify-assignments-set-db")),
        html.Div(
            dbc.Button(
                "Einstellung ausstehend",
                outline=True,
                color="primary",
                id="button-modify-assignments-generator-set-db",
                n_clicks=0,
            ),
        ),
    ],
    direction="horizontal",
    gap=3,

)

generator = html.Div(
    [
        html.Hr(className="mt-5"),
        html.H3("Generierung weiterer Daten"),
        html.P(
            """Hier können weitere Belegungsdaten und zugehörige Studierende für eine Veranstaltung / Studiengang durch Extrapolation / Interpolation bestehender Daten generiert werden.
                Dabei werden Wahrscheinlichkeitsverteilungen anhand aller existierenden Belegungsdaten und Studierendendaten einer Veranstaltung / Studiengang ermittelt,
                um so deren Belegungen annähernd, um ähnliche Belegungen und neuen Studierenden zu erweitern oder je nach Einstellung zu reduzieren. 
                Achtung! Falls zum Beispiel ein Großteil der Belegungen einer Veranstaltung den Status "Angemeldet" hat, so werden die generierten Daten diesen auch haben.
                Wenn wenige Belegungen in einer Veranstaltung vorzufinden sind, wird die Generierung wahrscheinlich kein realistisches Verhalten der Belegungen abbilden.
                Bei der Generierung handelt es sich also lediglich um Schätzungen.""",
        ),
        dbc.Stack(
            [
                html.Div(
                    html.H5(
                        "Anzahl an neuen Belegungen:",
                        className="text-center",
                    ),
                ),
                html.Div(
                    dbc.Input(
                        id="input-modify-assignments-generator-amount",
                        value=10,
                        size="sm",
                    ),
                ),
            ],
            direction="horizontal",
            gap=3,
        ),
        dbc.Stack(
            [
                html.Div(
                    html.H5(
                        "Start-Matrikelnummer:",
                        className="text-center",
                    ),
                ),
                html.Div(
                    dbc.Input(
                        id="input-modify-assignments-generator-matricule-number",
                        size="sm",
                    ),
                ),
                dbc.Tooltip(
                    """Falls angegeben, werden neue Studierende ab dieser Matrikelnummer generiert. 
                        Falls nicht angegeben, werden die Matrikelnummern automatisch ab der letzhöchsten vergeben. 
                        Sollte hier eine Start-Matrikelnummer angegeben werden, die mit bestehenden Matrikelnummern kollidiert, wird abgebrochen.""",
                    target="input-modify-assignments-generator-matricule-number",
                    placement="top",
                ),
            ],
            direction="horizontal",
            gap=3,
            className="mt-2",
        ),
        dbc.Stack(
            [
                html.Div(
                    html.H5(
                        "Ziel-Semester:",
                        className="text-center",
                    ),
                ),
                html.Div(
                    dbc.Input(
                        id="input-modify-assignments-generator-target-semester",
                        size="sm",
                    ),
                ),
                dbc.Tooltip(
                    """Diese Option ändert lediglich das Feld 'Semester' der neuen Belegungsdaten.
                        Damit kann also eine Veranstaltung für ein kommendes oder fiktives Semester anhand des aktuell eingestellten Semesters generiert werden.""",
                    target="input-modify-assignments-generator-target-semester",
                    placement="top",
                ),
            ],
            direction="horizontal",
            gap=3,
            className="mt-2",
        ),
        dbc.Stack(
            [
                html.Div(
                    html.H5(
                        "Status der neuen Belegungen:",
                        className="text-center",
                    ),
                ),
                html.Div(
                    dbc.Select(
                        id="input-modify-assignments-generator-status",
                        options=[
                            consts.RULE_SETTING_STATUS_ENROLLED,
                            consts.RULE_SETTING_STATUS_ACCEPTED,
                            consts.RULE_SETTING_STATUS_DENIED,
                            consts.RULE_SETTING_STATUS_SELF_DISENROLLED,
                            consts.RULE_SETTING_STATUS_PROPOSED,
                        ],
                        value=consts.RULE_SETTING_STATUS_ENROLLED,
                        size="sm",
                    ),
                ),
                dbc.Tooltip(
                    "Nützlich, um verschiedene Statuswerte zu einer"
                    " Veranstaltung hinzu zu generieren.",
                    target="input-modify-assignments-generator-status",
                    placement="top",
                ),
            ],
            direction="horizontal",
            gap=3,
            className="mt-2",
        ),
        dbc.Stack(
            [
                html.Div(
                    html.H5(
                        "Ursprüngliche Belegungen der Veranstaltung löschen?",
                        className="text-center",
                    ),
                ),
                html.Div(
                    dbc.Checkbox(
                        id="input-modify-assignments-generator-delete-existing",
                        value=False,
                    ),
                ),
                dbc.Tooltip(
                    "Löscht alle bestehenden Belegungsdaten der"
                    " Veranstaltung / des Studiengangs.",
                    target="input-modify-assignments-generator-delete-existing",
                    placement="top",
                ),
            ],
            direction="horizontal",
            gap=3,
            className="mt-2",
        ),
        html.Div(
            dbc.Button(
                "Starten",
                outline=False,
                color="warning",
                id="button-modify-assignments-generator-start",
                n_clicks=0,
            ),
            className="mt-2",
        ),
        html.Hr(className="mt-5"),
    ],
)

self_disenroll = html.Div(
    [
        html.H3("Selbstabmeldungen einspielen"),
        html.P(
            """Nützlich, um Belegungen einer Veranstaltung mit den Status 'Zugelassen' und 'Angemeldet' auf 'Selbstabmeldung' zu setzen und damit
                ein Selbstabmeldungs-Verhalten von Studierenden nachzuahmen. Die Chance wie viele Selbstabmeldungen in der gewählten Veranstaltung / Studiengang
                auftreten kann selbst eingestellt werden und ist standardmäßig auf 11.18% pro Belegung gestellt.
                Dieser Schätzwert wurde aus allen Belegungsdaten des Wintersemesters 2022 und Sommersemesters 2023 ermittelt.""",
        ),
        dbc.Stack(
            [
                html.Div(
                    html.H5(
                        "Wahrscheinlichkeit pro zugelassener Belegung: ",
                        className="text-center",
                    ),
                ),
                html.Div(
                    dbc.Input(
                        id="input-modify-assignments-disenroll-probability",
                        size="sm",
                        value="0.1118",
                    ),
                ),
            ],
            direction="horizontal",
            gap=3,
        ),
        html.Div(
            dbc.Button(
                "Starten",
                outline=False,
                color="warning",
                id="button-modify-assignments-start-disenroll",
                n_clicks=0,
            ),
            className="mt-2",
        ),
        html.Hr(className="mt-5"),
    ],
)

reset_status = html.Div(
    [
        html.H3("Status von Belegungen auf 'Angemeldet' zurücksetzen"),
        html.P(
            """Alle Belegungen einer Veranstaltung auf 'Angemeldet' zurücksetzen
            und getätigte Kombinationseinschreibungen löschen.""",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        [
                            html.I(className="bi bi-exclamation-square me-2"),
                            "Status in Veranstaltungs- / Studiengangs-ID"
                            " zurücksetzen",
                        ],
                        color="warning",
                        outline=False,
                        id="button-modify-assignments-reset-lecture",
                    ),
                    width=3,
                ),
                dbc.Col(
                    dbc.Button(
                        [
                            html.I(className="bi bi-exclamation-square me-2"),
                            "Status in aktuellem Semester zurücksetzen",
                        ],
                        color="warning",
                        outline=False,
                        id="button-modify-assignments-reset-semester",
                    ),
                    width=3,
                ),
                dbc.Col(
                    dbc.Button(
                        [
                            html.I(className="bi bi-exclamation-square me-2"),
                            "Status in kompletter Datenbank zurücksetzen",
                        ],
                        color="warning",
                        outline=False,
                        id="button-modify-assignments-reset-db",
                    ),
                    width=3,
                ),
            ],
        ),
        html.Div(className="mb-5")
    ],
)

layout_generate_new_assignments = html.Div(
    [
        dcc.Location(id="url-modify-assignments", refresh=False),
        loading_generator_fullscreen,
        input_database,
        input_target_id,
        generator,
        self_disenroll,
        reset_status,
    ],
    className="page-container",
)

layout = dbc.Container(
    layout_generate_new_assignments,
    fluid=False,
    className="main-container",
)


@callback(
    Output("select-modify-assignments-set-db", "options"),
    Input("url-modify-assignments", "search"),
)
def list_databases(search):
    """Return a list of available databases in filesystem."""
    list_db = db_utils.get_db_filelist()
    list_db.insert(0, "")
    return list_db


@callback(
    Output("button-modify-assignments-generator-set-target", "children"),
    Output("button-modify-assignments-generator-set-target", "outline"),
    Output("input-modify-assignments-set-target", "invalid"),
    Input("button-modify-assignments-generator-set-target", "n_clicks"),
    Input("select-modify-assignments-target-type", "value"),
    Input("input-modify-assignments-set-target", "value"),
)
def style_set_target_button(n_clicks, value_select, value_input):
    """Style the target input button to check if input is valid."""
    if value_select and value_input and not str.isspace(str(value_input)):
        try:
            value_input = int(value_input)

        except ValueError:
            return "Einstellung ausstehend", True, True

        button_option_is_set = [
            html.I(className="bi bi-check-square me-2"),
            "Einstellung gesetzt",
        ]
        return button_option_is_set, False, False

    return "Einstellung ausstehend", True, False


@callback(
    Output("button-modify-assignments-generator-set-db", "children"),
    Output("button-modify-assignments-generator-set-db", "outline"),
    Input("button-modify-assignments-generator-set-db", "n_clicks"),
    Input("select-modify-assignments-set-db", "value"),
)
def style_set_db_button(n_clicks, value):
    """Style the db input button to check if input is valid."""
    if value:
        button_option_is_set = [
            html.I(className="bi bi-check-square me-2"),
            "Einstellung gesetzt",
        ]
        return button_option_is_set, False

    return "Einstellung ausstehend", True


@callback(
    Output("input-modify-assignments-generator-amount", "invalid"),
    Input("input-modify-assignments-generator-amount", "value"),
)
def validate_input_generation_amount(value):
    """Validate if input for generation amount can be cast to int."""
    if value and not str.isspace(str(value)):
        try:
            value = int(value)

        except ValueError:
            return True
    # Empty field should also be invalid
    else:
        return True

    return False


@callback(
    Output("input-modify-assignments-generator-matricule-number", "invalid"),
    Input("input-modify-assignments-generator-matricule-number", "value"),
)
def validate_input_generation_matricule_number(value):
    """Validate if input for matricule number can be cast to int."""
    if value:
        try:
            value = int(value)

        except ValueError:
            return True

    return False


@callback(
    Output("input-modify-assignments-generator-target-semester", "invalid"),
    Input("input-modify-assignments-generator-target-semester", "value"),
)
def validate_input_generation_target_semester(value):
    """Validate if input for semester can be cast to int."""
    if value:
        try:
            value = int(value)

        except ValueError:
            return True

    return False


@callback(
    Output("button-modify-assignments-reset-lecture", "disabled"),
    Output("button-modify-assignments-reset-semester", "disabled"),
    Output("button-modify-assignments-reset-db", "disabled"),
    Output("button-modify-assignments-start-disenroll", "disabled"),
    Output("button-modify-assignments-generator-start", "disabled"),
    Input("button-modify-assignments-generator-set-db", "outline"),
    Input("button-modify-assignments-generator-set-target", "outline"),
)
def toggle_action_buttons(
    selected_db_invalid,
    selected_lecture_invalid,
):
    """Enable buttons if target ID and DB have been set.

    Check is done by looking if buttons are not outlined anymore.
    No outline means input is valid and reset can be done
    """
    # Database name and event id are set
    if not selected_db_invalid and not selected_lecture_invalid:
        return False, False, False, False, False

    # Only a database name is set -> activate buttons for status reset
    # of semester and whole db
    elif not selected_db_invalid and selected_lecture_invalid:
        return True, False, False, True, True

    return True, True, True, True, True


@callback(
    Output(
        "spinner-modify-assignments-fullscreen",
        "children",
        allow_duplicate=True,
    ),
    Input("select-modify-assignments-target-type", "value"),
    Input("input-modify-assignments-set-target", "value"),
    Input("select-modify-assignments-set-db", "value"),
    Input("button-modify-assignments-generator-start", "n_clicks"),
    Input("input-modify-assignments-generator-amount", "value"),
    Input("input-modify-assignments-generator-matricule-number", "value"),
    Input("input-modify-assignments-generator-target-semester", "value"),
    Input("input-modify-assignments-generator-status", "value"),
    Input("input-modify-assignments-generator-delete-existing", "value"),
    prevent_initial_call=True,
)
def run_generator(
    value_target_type,
    value_target_id,
    value_db,
    n_clicks_start_generation,
    value_generation_amount,
    value_generation_matricule_number,
    value_generation_target_semester,
    value_generation_status,
    value_generation_delete_existing,
):
    """Generate new assignments and corrseponding student data."""
    triggered_id = ctx.triggered_id

    # Assignment Generator
    if (
        n_clicks_start_generation
        and triggered_id == "button-modify-assignments-generator-start"
    ):
        # Number of new assignments
        value_generation_amount = (
            int(value_generation_amount) if value_generation_amount else None
        )

        # Input casting and validation - matricule number
        value_generation_matricule_number = validate_and_cast_int(
            value_generation_matricule_number,
            None,
        )

        # Input casting and validation - semester
        value_generation_target_semester = validate_and_cast_int(
            value_generation_target_semester,
            consts.RULE_SETTING_CURRENT_SEMESTER,
        )

        (
            generation_success,
            value_generation_target_semester,
        ) = model_generate_new_assignments.generate_new_assignments(
            value_target_id,
            value_generation_amount,
            value_db,
            target_type=value_target_type,
            database_name_output=None,
            start_matricule_number=value_generation_matricule_number,
            semester_to_generate_for=value_generation_target_semester,
            delete_lecture_assignments=value_generation_delete_existing,
            assignment_status_to_use=value_generation_status,
        )
        if generation_success:
            return (
                dbc.Alert(
                    f"Generierung von {value_generation_amount} neuen"
                    f" Belegungen und zugehörigen Studierenden für"
                    f" {value_target_type} {value_target_id} im Semester"
                    f" {value_generation_target_semester} abgeschlossen.",
                    dismissable=True,
                    color="primary",
                ),
            )
        else:
            return (
                dbc.Alert(
                    "Generierung fehlgeschlagen."
                    " Siehe Konsolenausgabe oder Log.",
                    dismissable=True,
                    color="danger",
                ),
            )

    return ""


@callback(
    Output(
        "spinner-modify-assignments-fullscreen",
        "children",
        allow_duplicate=True,
    ),
    Input("select-modify-assignments-target-type", "value"),
    Input("input-modify-assignments-set-target", "value"),
    Input("select-modify-assignments-set-db", "value"),
    Input("button-modify-assignments-start-disenroll", "n_clicks"),
    Input("input-modify-assignments-disenroll-probability", "value"),
    prevent_initial_call=True,
)
def run_disenroll(
    value_target_type,
    value_target_id,
    value_db,
    n_clicks_start_disenroll,
    value_disenroll_probability,
):
    """Set status of assignments to disenrolled by chance."""
    triggered_id = ctx.triggered_id

    # Self disenroll
    if (
        n_clicks_start_disenroll
        and triggered_id == "button-modify-assignments-start-disenroll"
    ):
        # Cast string inputs
        value_target_id = validate_and_cast_int(value_target_id, None)

        # Use float for probability
        if isinstance(value_disenroll_probability, str) and not str.isspace(
            value_disenroll_probability,
        ):
            value_disenroll_probability = float(value_disenroll_probability)

        count = (
            model_trigger_self_disenrollment.trigger_self_disenrollment_chance(
                value_target_id,
                value_db,
                value_target_type,
                value_disenroll_probability,
            )
        )

        return (
            dbc.Alert(
                f"Es wurden {count} Belegungen auf Status"
                f" '{consts.RULE_SETTING_STATUS_SELF_DISENROLLED}' gesetzt",
                dismissable=True,
                color="primary",
            ),
        )

    return ""


@callback(
    Output(
        "spinner-modify-assignments-fullscreen",
        "children",
        allow_duplicate=True,
    ),
    Input("select-modify-assignments-target-type", "value"),
    Input("input-modify-assignments-set-target", "value"),
    Input("select-modify-assignments-set-db", "value"),
    Input("button-modify-assignments-reset-lecture", "n_clicks"),
    Input("button-modify-assignments-reset-semester", "n_clicks"),
    Input("button-modify-assignments-reset-db", "n_clicks"),
    prevent_initial_call=True,
)
def run_reset(
    value_target_type,
    value_target_id,
    value_db,
    n_clicks_reset_lecture,
    n_clicks_reset_semester,
    n_clicks_reset_db,
):
    """Reset status to enrolled for lecture, study program, semester and db."""
    triggered_id = ctx.triggered_id

    # Reset status lecture / study program
    if (
        n_clicks_reset_lecture
        and triggered_id == "button-modify-assignments-reset-lecture"
    ):
        # Cast string inputs
        value_target_id = validate_and_cast_int(value_target_id, None)

        (
            changed_assignments,
            deleted_event_combinations,
        ) = model_reset_assignment_status.reset_assignment_status(
            value_db,
            target_id=value_target_id,
            target_type=value_target_type,
            semester=None,
        )
        return (
            dbc.Alert(
                f"Der Status von {changed_assignments} Belegungen wurde auf"
                f" '{consts.RULE_SETTING_STATUS_ENROLLED}' gesetzt und"
                f" {deleted_event_combinations} Kombotrigger wurden gelöscht.",
                dismissable=True,
                color="primary",
            ),
        )

    # Reset status semester
    elif (
        n_clicks_reset_semester
        and triggered_id == "button-modify-assignments-reset-semester"
    ):
        (
            changed_assignments,
            deleted_event_combinations,
        ) = model_reset_assignment_status.reset_assignment_status(
            value_db,
            target_id=None,
            target_type=None,
            semester=consts.RULE_SETTING_CURRENT_SEMESTER,
        )
        return (
            dbc.Alert(
                f"Der Status von {changed_assignments} Belegungen wurde auf"
                f" '{consts.RULE_SETTING_STATUS_ENROLLED}' gesetzt und"
                f" {deleted_event_combinations} Kombotrigger wurden gelöscht.",
                dismissable=True,
                color="primary",
            ),
        )

    # Reset status DB
    elif (
        n_clicks_reset_db
        and triggered_id == "button-modify-assignments-reset-db"
    ):
        (
            changed_assignments,
            deleted_event_combinations,
        ) = model_reset_assignment_status.reset_assignment_status(
            value_db,
            target_id=None,
            target_type=None,
            semester=None,
        )
        return (
            dbc.Alert(
                f"Der Status von {changed_assignments} Belegungen wurde auf"
                f" '{consts.RULE_SETTING_STATUS_ENROLLED}' gesetzt und"
                f" {deleted_event_combinations} Kombotrigger wurden gelöscht.",
                dismissable=True,
                color="primary",
            ),
        )

    return ""
