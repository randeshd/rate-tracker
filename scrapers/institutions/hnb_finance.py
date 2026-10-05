from ..core.fetch import fetch
from ..core.models import Institution, Rate
from ..core.parse import soup_of, table_under_heading
from ..core.rows import rates_from_rows, column_index

INSTITUTION = Institution(
    id="hnb_finance",
    name="HNB Finance",
    type="finance",
    source_url="https://www.hnbfinance.lk/fixed-deposits/",
)


def scrape() -> list[Rate]:
    # robots.txt asks for a 10 second crawl delay; the shared fetcher honours it.
    soup = soup_of(fetch(INSTITUTION.source_url))
    rows = table_under_heading(soup, r"^Interest Rates$")
    return rates_from_rows(rows, rate_col=column_index(rows, "Maturity (p.a.)"))
