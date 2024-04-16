$pythonVersion = python --version 2>&1
if ($pythonVersion -notmatch "Python 3.12.2") {
    Write-Output "Python 3.12.2 oder höher ist nicht installiert."
    Write-Output "Bitte von der offiziellen Python-Website herunterladen und installieren."
    exit
}
if ($env:VIRTUAL_ENV) {
    Write-Output "Python Virtual Environment ist bereits aktiviert."
} else {
    if (!(Test-Path -Path venv)) {
        Write-Output "Python Virtual Environment existiert nicht. Erstellt venv..."
        python -m venv venv
        Write-Output "Aktiviere Python Virtual Environment..."
        .\venv\Scripts\Activate.ps1
        Write-Output "Aktualisiere pip..."
        python -m pip install --upgrade pip
        if (Test-Path -Path requirements.txt) {
            Write-Output "Installiere vorausgesetzte Python Pakete..."
            python -m pip install -r requirements.txt
        }
    } else {
        Write-Output "Aktiviere Python Virtual Environment..."
        .\venv\Scripts\Activate.ps1
    }
}
Write-Output "Starte Hauptprogramm app.py..."
python app.py
