"""404 page to show if page is not found."""

import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(__name__)

layout = dbc.Container(
    html.H1("404 - Seite nicht gefunden"),
    fluid=False,
    className="main-container",
)