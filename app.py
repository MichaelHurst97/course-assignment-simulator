import dash
from dash import html
# Open wenbrowser on start: https://stackoverflow.com/questions/54235347/open-browser-automatically-when-python-code-is-executed/54235461#54235461 (last accessed: 14.04.2024)
import webbrowser

import utils.constants as consts
import components.navbar.layout_navbar as layout_navbar

app = dash.Dash(__name__, use_pages=True, title=consts.APP_NAME)

app.layout = html.Div([layout_navbar.layout, dash.page_container])

if __name__ == "__main__":
    webbrowser.open_new("http://localhost:8050")
    app.run_server(debug=False)
