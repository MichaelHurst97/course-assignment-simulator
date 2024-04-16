"""Shared logger object with custom format and console colors."""

import datetime
import logging
import os
from io import StringIO
from pathlib import Path

from colorama import just_fix_windows_console

import utils.constants as consts

# Fix missing colors when running app through a windows console
# https://pypi.org/project/colorama/ (last accessed: 14.04.2024)
just_fix_windows_console()

# Fix flask logger logging every post http update
# https://community.plotly.com/t/prevent-post-dash-update-component-http-1-1-messages/11132 (last accessed: 14.04.2024)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Formatting to use for logger output, with different colors for each log level
FORMAT = (
    "%(asctime)s - %(levelname)s - %(filename)s - "
    "%(message)s (Line: %(lineno)d)"
)

LEVELS = {
    logging.DEBUG: f"{FORMAT}",
    logging.INFO: f"{FORMAT}",
    logging.WARNING: f"{consts.CONSOLE_YELLOW}{FORMAT}{consts.CONSOLE_ENDCMD}",
    logging.ERROR: f"{consts.CONSOLE_RED}{FORMAT}{consts.CONSOLE_ENDCMD}",
    logging.CRITICAL: (
        f"{consts.CONSOLE_RED_BOLD}{FORMAT}{consts.CONSOLE_ENDCMD}"
    ),
}


def console_formatter(log_record):
    """Add colors to log levels."""
    log_format = LEVELS.get(log_record.levelno)
    formatter = logging.Formatter(log_format)
    return formatter.format(log_record)


# Log file creation
logs_folder = consts.FOLDER_LOGS
if not Path.exists(logs_folder):
    Path.mkdir(logs_folder)
current_datetime = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
log_file = os.path.realpath(Path(logs_folder, f"log_{current_datetime}.txt"))
logging.basicConfig(
    filename=log_file,
    level=consts.LOG_LEVEL,
    encoding="utf-8",
    format=FORMAT,
)

# Shared logger for all modules
logger = logging.getLogger()

# Stream handler for dash ui output
logger.log_stream = StringIO()
stream_handler = logging.StreamHandler(logger.log_stream)
stream_handler.setFormatter(logging.Formatter(fmt=FORMAT))
stream_handler.format = console_formatter
logger.addHandler(stream_handler)

# Stream handler for console
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(fmt=FORMAT))
console_handler.format = console_formatter
logger.addHandler(console_handler)
