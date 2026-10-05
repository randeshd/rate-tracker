from ..core.fetch import fetch
from ..core.models import Institution, Rate
from ..core.parse import soup_of, table_under_heading
from ..core.rows import rates_from_rows, column_index

INSTITUTION = Institution(
    id="vallibel",
    name="Vallibel Finance",
    type="finance",
    source_url="https://vallibelfinance.com/fixed-deposits/",
)


def scrape() -> list[Rate]:
    soup = soup_of(fetch(INSTITUTION.source_url))
    rows = table_under_heading(soup, r"^Normal Citizen")
    return rates_from_rows(rows, rate_col=column_index(rows, "Maturity"))
