"""Utils concerning project licenses."""

import json
import subprocess
from pathlib import Path

import utils.constants as consts


def create_license_files():
    """Extract LICENSE texts of third party packages used in this project."""
    licenses_dir = Path(consts.FOLDER_ROOT, "LICENSES")
    json_file_path = Path(licenses_dir, "third_party_package_licenses.json")

    Path.mkdir(licenses_dir, exist_ok=True)

    # Use pip-licenses module to read out installed package licenses
    # Licenses will be output as a json file
    # https://pypi.org/project/pip-licenses/ (last accessed: 14.04.2024)
    subprocess.run(
        [
            "pip-licenses",
            "--with-license-file",  # Get the license text,
            "--no-license-path",  # But not the path
            "--with-urls",
            "--format=json",
            "--output-file=" + str(json_file_path),
        ],
        check=False,
    )

    # Read the output file
    with Path.open(json_file_path) as f:
        packages = json.load(f)

    # Create directories named like the packages of this project
    for package in packages:
        Path.mkdir(Path(licenses_dir, package["Name"]), exist_ok=True)

        # Write License text to their newly created folder
        with Path.open(
            Path(licenses_dir, package["Name"], "LICENSE"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(package["LicenseText"])


if __name__ == "__main__":
    create_license_files()
