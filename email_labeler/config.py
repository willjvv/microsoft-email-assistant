import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES_FILE = ROOT / "categories.json"
PROCESSED_FILE = ROOT / "processed.json"

DEFAULT_CATEGORIES = [
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


def load_categories():
    if not CATEGORIES_FILE.exists():
        save_categories(DEFAULT_CATEGORIES)

    try:
        data = json.loads(CATEGORIES_FILE.read_text(encoding="utf-8"))
        categories = data.get("categories", [])
        return [str(x).strip() for x in categories if str(x).strip()]
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CATEGORIES.copy()


def save_categories(categories):
    CATEGORIES_FILE.write_text(
        json.dumps({"categories": categories}, indent=2),
        encoding="utf-8",
    )
