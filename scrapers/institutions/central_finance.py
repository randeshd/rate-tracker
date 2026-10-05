from ..core.fetch import fetch
from ..core.models import Institution, Rate
from ..core.parse import soup_of, table_rows
from ..core.rows import rates_from_rows, column_index

INSTITUTION = Institution(
    id="central_finance",
    name="Central Finance",
    type="finance",
    source_url="https://cf.lk/interest-rates/",
)


def _product_table(soup, anchor_id: str) -> list[list[str]]:
    section = soup.find(id=anchor_id)
    table = (section.find("table") or section.find_next("table")) if section else None
    if table is None:
        raise ValueError(f"table not found: {anchor_id}")
    return table_rows(table)


def scrape() -> list[Rate]:
    soup = soup_of(fetch(INSTITUTION.source_url))
    rates = []
    # CF Excel covers 1-6 months, CF Term covers 9 months and longer
    for anchor in ("cf-excel", "cf-term"):
        rows = _product_table(soup, anchor)
        rates += rates_from_rows(rows, rate_col=column_index(rows, "Maturity"))
    return rates
