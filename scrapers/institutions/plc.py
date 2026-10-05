from ..core.fetch import fetch
from ..core.models import Institution, Rate
from ..core.parse import soup_of, table_under_heading
from ..core.rows import rates_from_rows

INSTITUTION = Institution(
    id="plc",
    name="People's Leasing & Finance",
    type="finance",
    source_url="https://www.plc.lk/products/fixed-deposits-savings/fixed-deposits/",
)


def scrape() -> list[Rate]:
    soup = soup_of(fetch(INSTITUTION.source_url))
    # data rows: Tenor | Maturity rate | AER | Monthly rate | AER
    rows = table_under_heading(soup, r"Normal Fixed Deposit rates")
    return rates_from_rows([r for r in rows if len(r) == 5], rate_col=1)
