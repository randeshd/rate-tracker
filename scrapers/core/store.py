"""Read/write data files: data/latest.json and data/history/rates.csv."""
import csv
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
LATEST = DATA_DIR / "latest.json"
HISTORY = DATA_DIR / "history" / "rates.csv"
HISTORY_FIELDS = ["date", "institution_id", "tenure_months", "nominal_pct", "aer_pct", "note"]


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def append_history(day: str, institution_id: str, rates: list[dict]) -> None:
    """Add one row per tenure for the day; re-running on the same day does not duplicate."""
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    if HISTORY.exists():
        with HISTORY.open(newline="") as f:
            rows = [r for r in csv.DictReader(f) if not (r["date"] == day and r["institution_id"] == institution_id)]
    for r in rates:
        rows.append({"date": day, "institution_id": institution_id, **r})
    rows.sort(key=lambda r: (r["date"], r["institution_id"], int(r["tenure_months"])))
    with HISTORY.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HISTORY_FIELDS)
        w.writeheader()
        w.writerows(rows)
