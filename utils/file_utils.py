"""Utils for file reading and writing."""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .logger import logger


def get_folder(folder: Path):
    """Passthrough function to create a folder if not found.

    This way it's certain that a folder exists and all project folders
    are present. Use with cautiously.
    """
    if not Path.exists(folder):
        Path.mkdir(folder)

    return folder


def check_file_presence(folder: Path, filename: str):
    """Check if a given filename exists in a folder."""
    if folder is not None and filename is not None:
        file_path = Path(folder, filename)
        return Path.is_file(file_path)

    return None


def read_json(folder: Path, filename: str):
    """Check if a json file exists and load it.

    Returns the json file structure and the filename.
    """
    file_path = Path(folder, filename)
    try:
        with Path.open(file_path, encoding="utf-8") as f:
            return json.load(f)

    except FileNotFoundError:
        logger.exception(f"Datei '{file_path}' nicht vorhanden.")
        raise


def write_json(data, folder: Path, filename: str):
    """Serialize a data structure as json file to a given folder."""
    file_path = Path(folder, filename)
    try:
        with Path.open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return True

    except OSError:
        logger.error(f"Datei '{file_path}' konnte nicht geschrieben werden.")
        raise


def get_query_string_params(query_string: str):
    """Return query string parameters."""
    return parse_qs(urlparse(query_string).query)


def get_query_string(query_string: str, parameter: str):
    """Return a single query string for a parameter."""
    params = get_query_string_params(query_string)
    for key, value in params.items():
        if key == parameter:
            # Query string output is in list format, so change list to string
            return "".join(value)
    return None


def get_filesize(path_to_file: Path):
    """Return the filesize of a file as string in megabytes."""
    try:
        size = Path.stat(path_to_file).st_size
        size_mb = size / 1024 / 1024
        size_mb = str(round(size_mb, 3)) + " MB"
        return size_mb

    except OSError:
        logger.error(
            f"Fehler beim ermitteln der Dateigröße für '{path_to_file}'",
        )
        raise


# https://stackoverflow.com/questions/1976007/what-characters-are-forbidden-in-windows-and-linux-directory-names (last accessed: 14.04.2024)
def remove_invalid_input_field_characters(input_value: str):
    """Replace chars that aren't allowed in windows paths by a whitespace."""
    forbidden_characters = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    for character in forbidden_characters:
        input_value = input_value.replace(character, " ")
    return input_value
