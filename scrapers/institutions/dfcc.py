import json
import re

from ..core.fetch import fetch
from ..core.models import Institution, Rate
from ..core.parse import parse_tenure, parse_pct

INSTITUTION = Institution(
    id="dfcc",
    name="DFCC Bank",
    type="bank",
    source_url="https://www.dfcc.lk/rates-and-tariff?tab=fixed_deposits",
)

# The page embeds its rate tables as escaped JSON blocks: ..."title":"<table>","content":{<row>}...
_BLOCK = re.compile(r'"title":"([^"]*)","content":(\{[^{}]*\})')


def _rows(html: str) -> dict[str, list[dict]]:
    text = html.replace('\\"', '"')
    tables: dict[str, list[dict]] = {}
    for title, content in _BLOCK.findall(text):
        try:
            row = json.loads(content)
        except json.JSONDecodeError:
            continue
        rows = tables.setdefault(title.strip().lower(), [])
        if row not in rows:
            rows.append(row)
    return tables


def scrape() -> list[Rate]:
    tables = _rows(fetch(INSTITUTION.source_url).decode("utf-8", errors="replace"))
    rates = []
    # Standard FD: one row per payout type, one key per tenure ("3_month", "2_year")
    for title in ("fd rates 1 year and below", "fd rates 1 year and above"):
        nominal = next((r for r in tables.get(title, []) if r.get("category") == "Nominal"), None)
        if nominal is None:
            raise ValueError(f"table not found: {title}")
        for key, value in nominal.items():
            tenure, pct = parse_tenure(key.replace("_", " ")), parse_pct(value)
            if key != "category" and tenure and pct:
                rates.append(Rate(tenure, pct))
    # Special FD quoted in days (non-renewable)
    for row in tables.get("special fixed deposit product", []):
        days = re.fullmatch(r"\s*(\d+)\s*days?\s*", row.get("tenor", ""), re.I)
        pct = parse_pct(row.get("nominal_rate", ""))
        if days and pct:
            rates.append(Rate.for_days(int(days.group(1)), pct, "Special FD (non renewable)"))
    return rates
