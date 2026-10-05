from ..core.fetch import fetch
from ..core.models import Institution, Rate
from ..core.parse import soup_of, table_rows
from ..core.rows import rates_from_rows

INSTITUTION = Institution(
    id="lolc_finance",
    name="LOLC Finance",
    type="finance",
    source_url="https://www.lolcfinance.com/rates-and-returns/interest-rates/",
)


def scrape() -> list[Rate]:
    soup = soup_of(fetch(INSTITUTION.source_url))
    # "General / Senior Citizen Fixed Deposits" tab (the other tab is Wakala investments)
    pane = soup.find(id="GeneralFD")
    table = pane.find("table") if pane else None
    if table is None:
        raise ValueError("General FD table not found")
    # data rows: Months | Monthly simple, AER | Annually simple, AER | Maturity simple, AER
    rows = [[r[0] + " months"] + r[1:] for r in table_rows(table) if len(r) == 7 and r[0].isdigit()]
    return rates_from_rows(rows, rate_col=5)
