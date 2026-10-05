from ..core.fetch import fetch
from ..core.models import Institution, Rate
from ..core.parse import soup_of, table_rows
from ..core.rows import rates_from_rows

INSTITUTION = Institution(
    id="singer_finance",
    name="Singer Finance",
    type="finance",
    source_url="https://www.singerfinance.com/products/fixed-deposit/standard-fixed-deposits",
)


def scrape() -> list[Rate]:
    soup = soup_of(fetch(INSTITUTION.source_url))
    for table in soup.find_all("table"):
        rows = table_rows(table)
        if rows and "interest paid at maturity" in " ".join(rows[0]).lower():
            # data rows: Period | Monthly rate, AER | At maturity rate, AER | Annually rate, AER
            return rates_from_rows([r for r in rows if len(r) == 7], rate_col=3)
    raise ValueError("standard fixed deposit table not found")
