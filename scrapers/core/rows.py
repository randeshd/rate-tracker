"""Turn table rows into Rate objects."""
import re

from .models import Rate
from .parse import parse_pct, parse_tenure


def make_rate(term: str, pct_text: str, note: str = "") -> Rate | None:
    """Build a Rate from a term cell ('6 Months', '200 Days', '2 Years') and a rate cell."""
    pct = parse_pct(pct_text)
    if pct is None:
        return None
    days = re.search(r"(\d+)\s*days?", term, re.I)
    if days:
        return Rate.for_days(int(days.group(1)), pct, note)
    tenure = parse_tenure(term)
    return Rate(tenure, pct, note) if tenure else None


def rates_from_rows(rows: list[list[str]], rate_col: int, term_col: int = 0, note: str = "") -> list[Rate]:
    out = []
    for row in rows:
        if len(row) > max(rate_col, term_col):
            rate = make_rate(row[term_col], row[rate_col], note)
            if rate:
                out.append(rate)
    return out


def column_index(rows: list[list[str]], name: str, occurrence: int = 0) -> int:
    """Index of the nth header cell equal to name (case-insensitive) in the first rows."""
    for row in rows[:3]:
        hits = [i for i, c in enumerate(row) if c.strip().lower() == name.lower()]
        if len(hits) > occurrence:
            return hits[occurrence]
    raise ValueError(f"column not found: {name}")
