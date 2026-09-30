import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDERS_FILE = ROOT / "folders.json"
PROCESSED_FILE = ROOT / "processed.json"

DEFAULT_FOLDERS = [
    "Client",
    "Project",
    "Scheduling",
    "Travel",
    "Budget",
    "Invoice",
    "Contract",
    "Production",
    "Post Production",
    "Internal",
    "Newsletter",
    "Personal",
    "Urgent",
    "Other",
]


def load_folders():
    if not FOLDERS_FILE.exists():
        save_folders(DEFAULT_FOLDERS)

    try:
        data = json.loads(FOLDERS_FILE.read_text(encoding="utf-8"))
        folders = data.get("folders", [])
        return [str(x).strip() for x in folders if str(x).strip()]
    except (json.JSONDecodeError, OSError):
        return DEFAULT_FOLDERS.copy()


def save_folders(folders):
    FOLDERS_FILE.write_text(
        json.dumps({"folders": folders}, indent=2),
        encoding="utf-8",
    )
