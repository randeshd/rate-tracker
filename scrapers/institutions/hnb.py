import json

from ..core.fetch import fetch
from ..core.models import Institution, Rate
from ..core.parse import clean, parse_tenure, parse_pct

INSTITUTION = Institution(
    id="hnb",
    name="HNB",
    type="bank",
    source_url="https://www.hnb.lk/interest-rates",
)

# The rates page is a JavaScript app; this is the JSON feed it loads its tables from.
API_URL = "https://venus.hnb.lk/api/get_interest_rates_contents"


def _column(columns: list[str], *names: str) -> int | None:
    lowered = [clean(c).lower() for c in columns]
    for name in names:
        if name in lowered:
            return lowered.index(name)
    return None


def scrape() -> list[Rate]:
    feed = json.loads(fetch(API_URL))
    divisions = [
        div
        for category in feed["data"]
        for sub in category["interest_rate_sub_category"]
        if clean(sub["name"]).lower() == "fixed deposits"
        for div in sub["sub_category_division_approved"]
    ]
    rates = []
    for div in divisions:
        title = clean(div["title"]).lower()
        if title == "fixed deposits interest rates":
            special = False
        elif title == "special fixed deposits":
            special = True
        else:
            continue  # senior citizen / Sathkara products are out of scope
        for t in div["table_data_approved"]:
            table = json.loads(t["data"])
            rate_col = _column(table["columns"], "maturity", "rate")
            comment_col = _column(table["columns"], "special comments")
            if rate_col is None:
                continue
            for row in table["rows"]:
                tenure, pct = parse_tenure(row[0]), parse_pct(row[rate_col])
                if not (tenure and pct):
                    continue
                note = ""
                if special:
                    comment = clean(row[comment_col]) if comment_col is not None else ""
                    note = "Special FD" + (f" ({comment.lower()})" if comment else "")
                rates.append(Rate(tenure, pct, note))
    return rates
