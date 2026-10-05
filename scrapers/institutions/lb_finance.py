from ..core.fetch import fetch
from ..core.models import Institution, Rate
from ..core.parse import soup_of, table_rows
from ..core.rows import rates_from_rows

INSTITUTION = Institution(
    id="lb_finance",
    name="LB Finance",
    type="finance",
    source_url="https://www.lbfinance.com/fixed-deposits/fixed-deposits",
)


def scrape() -> list[Rate]:
    soup = soup_of(fetch(INSTITUTION.source_url))
    for table in soup.find_all("table"):
        rows = table_rows(table)
        header = " ".join(" ".join(r) for r in rows[:2]).lower()
        if "normal" in header and "senior" in header and "maturity" in header:
            # data rows: Period | Normal Monthly | AER | Normal Maturity | AER | Senior ...
            return rates_from_rows([r for r in rows if len(r) == 9], rate_col=3)
    raise ValueError("fixed deposit rates table not found")
