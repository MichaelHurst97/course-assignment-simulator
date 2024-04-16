"""UI layout for home page based on dash."""

import configparser
import importlib
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, ctx, dcc, html

import utils.constants as consts
from utils.logger import logger

dash.register_page(
    __name__,
    path=consts.PAGE_HOME_URL,
    title=consts.PAGE_HOME_TITLE_NAME,
    name=consts.PAGE_HOME_TITLE_NAME,
)


def card(
    text_title: str,
    text_description: str,
    text_button: str,
    icon_style: str,
    link: str,
):
    """Create homepage card html code via reusable function."""
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.I(
                        className=f"bi {icon_style} ",
                        style={"fontSize": "3rem"},
                    ),
                    html.H4(text_title, className="card-title"),
                    html.P(text_description, className="card-text"),
                ],
            ),
            dbc.CardFooter(
                dbc.Button(text_button, href=link, color="primary"),
            ),
        ],
    )


alert_semester_changed = html.Div(
    [
        dbc.Alert(
            "Semester übernommen.",
            id="alert-home-semester",
            is_open=False,
            duration=2000,
        ),
    ],
)

alert_settings_changed = html.Div(
    [
        dbc.Alert(
            "Einstellungen übernommen.",
            id="alert-home-settings",
            is_open=False,
            duration=2000,
        ),
    ],
)

input_semester = dbc.Stack(
    [
        html.Div(
            html.H3("Semester einstellen: ", className="text-center"),
        ),
        html.Div(
            dbc.Input(
                id="input-home-semester",
            ),
        ),
        dbc.Tooltip(
            "Muss mit dem Format innerhalb der Datenbank übereinstimmen."
            " In der Regel '20231' statt 'SoSe23'",
            target="input-home-semester",
            placement="top",
        ),
        html.Div(
            dbc.Button(
                "Übernehmen",
                outline=True,
                color="primary",
                id="button-home-semester",
                n_clicks=0,
            ),
        ),
    ],
    direction="horizontal",
    gap=3,
)


button_open_settings = (
    dbc.Button(
        [html.I(className="bi bi-gear me-2"), "Weitere Einstellungen"],
        color="primary",
        class_name="",
        id="button-home-settings",
        n_clicks=0,
    ),
)

header_settings = dbc.Row(
    [dbc.Col(input_semester), dbc.Col(button_open_settings)],
    style={"textAlign": "right"},
)


cards_row_data_creation = html.Div(
    [
        html.Hr(className="mt-4"),
        html.H2("Neue Belegungsdaten einspielen und hinzu generieren"),
        dbc.CardGroup(
            [
                card(
                    "Abbild aus Datei importieren",
                    "Einspielen eines Datenbank-Abbilds in ein"
                    " Datenbank-Format für den Simulator.",
                    "Öffnen",
                    "bi-database-add",
                    f"{consts.PAGE_IMPORT_DB_FILE_URL}",
                ),
                card(
                    "Daten anhand Import hinzu generieren oder verändern",
                    "Weitere Belegungsdaten durch Extrapolation /"
                    " Interpolation bestehender Daten erstellen, Selbstabmeldungen auslösen oder Datenbank zurücksetzen.",
                    "Öffnen",
                    "bi-stars",
                    f"{consts.PAGE_GENERATOR_URL}",
                ),
            ],
        ),
    ],
)


cards_row_simulator = html.Div(
    [
        html.Hr(className="mt-5"),
        html.H2("Mit vorhandenen Daten weitermachen"),
        dbc.CardGroup(
            [
                card(
                    "Simulator & Datenbank-Manager",
                    "Simulation einer Belegungsrunde anhand eigener"
                    " Belegungsregeln. Ermöglicht auch die Verwaltung"
                    " importierter Belegungsdaten.",
                    "Öffnen",
                    "bi-book",
                    f"{consts.PAGE_DB_MANAGER_URL}",
                ),
                card(
                    "Ergebnis Visualisierungs-Tool",
                    "Darstellung und Erkundung von Simualtions-Ergebnissen."
                    " Ermöglicht auch den Vergleich mehrerer"
                    " Simulations-Ergebnisse.",
                    "Öffnen",
                    "bi-binoculars",
                    f"{consts.PAGE_VISUALIZER_URL}",
                ),
            ],
        ),
    ],
)


settings_modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Einstellungen")),
                dbc.ModalBody(
                    [
                        html.Div(
                            [
                                dcc.Textarea(
                                    id="textarea-home-settings",
                                    style={"width": "100%", "height": "60vh"},
                                ),
                            ],
                        ),
                    ],
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "Abbrechen",
                            id="button-home-settings-cancel",
                            outline=True,
                            className="ms-auto",
                            n_clicks=0,
                        ),
                        dbc.Button(
                            "Übernehmen",
                            id="button-home-settings-save",
                            className="me-0",
                            n_clicks=0,
                        ),
                    ],
                ),
            ],
            size="lg",
            id="modal-home-settings",
        ),
    ],
)


footer = html.Div(
    [
        html.Hr(className="mt-5"),
        html.P(
            [
                dcc.Link("Über diese Anwendung", href=consts.PAGE_ABOUT_URL),
                f" - 2024 Version {consts.APP_VERSION}",
            ],
            style={"textAlign": "center"},
        ),
    ],
)


layout_home = html.Div(
    [
        settings_modal,
        alert_semester_changed,
        alert_settings_changed,
        header_settings,
        cards_row_data_creation,
        cards_row_simulator,
        footer,
    ],
    className="page-container",
)


layout = dbc.Container(layout_home, fluid=False, className="main-container")


@callback(
    Output("alert-home-semester", "is_open"),
    Output("input-home-semester", "value"),
    Input("button-home-semester", "n_clicks"),
    Input("button-home-settings", "n_clicks"),
    Input("button-home-settings-save", "n_clicks"),
    [State("alert-home-semester", "is_open")],
    [State("input-home-semester", "value")],
)
def apply_settings(
    n_clicks,
    n_clicks_modal,
    n_clicks_modal_save,
    is_open,
    value_semester,
):
    """Apply the semester typed into the input field as setting or the changed
    settings via textarea. Reloads the consts import for setting variables
    to change.
    """
    triggered_id = ctx.triggered_id

    if n_clicks and triggered_id == "button-home-semester":
        consts.change_setting(
            "Rule Application",
            "current_semester",
            value_semester,
        )
        # Reload import for changed setting to change at runtime
        importlib.reload(consts)
        value_semester = consts.RULE_SETTING_CURRENT_SEMESTER
        return not is_open, value_semester

    # Reload when settings modal is saves or closes
    elif (
        n_clicks_modal
        and triggered_id == "button-home-settings"
        or n_clicks_modal_save
        and triggered_id == "button-home-settings-save"
    ):
        importlib.reload(consts)
        value_semester = consts.RULE_SETTING_CURRENT_SEMESTER
        return is_open, value_semester

    value_semester = consts.RULE_SETTING_CURRENT_SEMESTER
    return is_open, value_semester


@callback(
    Output("textarea-home-settings", "value"),
    Input("modal-home-settings", "is_open"),
)
def read_settings_file(is_open):
    """Load settings file content to textarea of modal when modal opens."""
    if is_open:
        settings = configparser.ConfigParser()
        settings.read(consts.SETTINGS_FILE)

        with Path.open(consts.SETTINGS_FILE, encoding="utf-8") as f:
            return f.read()

    return None


@callback(
    Output("modal-home-settings", "is_open"),
    Output("alert-home-settings", "is_open"),
    Input("button-home-settings", "n_clicks"),
    Input("button-home-settings-save", "n_clicks"),
    Input("button-home-settings-cancel", "n_clicks"),
    [
        State("modal-home-settings", "is_open"),
        State("alert-home-settings", "is_open"),
        State("textarea-home-settings", "value"),
    ],
)
def toggle_settings_modal(
    n_clicks,
    n_clicks_save,
    n_clicks_cancel,
    is_open_modal,
    is_open_alert,
    value_textarea,
):
    """Control opening / closing of settings modal and it's saving
    functionality.
    """
    triggered_id = ctx.triggered_id

    # Open / Close Modal
    if (
        n_clicks
        and triggered_id == "button-home-settings"
        or n_clicks_cancel
        and triggered_id == "button-home-settings-cancel"
    ):
        return not is_open_modal, is_open_alert

    # Close Modal and save textarea to settings file
    elif n_clicks_save and triggered_id == "button-home-settings-save":
        with Path.open(consts.SETTINGS_FILE, "w+", encoding="utf-8") as f:
            f.write(value_textarea)
        importlib.reload(consts)
        logger.info("Einstellungs-Datei mit Textarea Input geschrieben")
        return not is_open_modal, not is_open_alert

    return is_open_modal, is_open_alert
