from ..core.fetch import fetch
from ..core.models import Institution, Rate
from ..core.parse import soup_of, table_under_heading
from ..core.rows import rates_from_rows, column_index

INSTITUTION = Institution(
    id="cdb",
    name="CDB",
    type="finance",
    source_url="https://www.cdb.lk/rates-tariffs",
)


def scrape() -> list[Rate]:
    soup = soup_of(fetch(INSTITUTION.source_url))
    rows = table_under_heading(soup, r"^CDB Fixed Deposit$")
    rates = rates_from_rows(rows, rate_col=column_index(rows, "Maturity Interest"))
    try:  # special tenures, e.g. "13 Months (CDB Fixed Deposit)"; skip the senior citizen rows
        special = [r for r in table_under_heading(soup, r"^Special Tenures$") if "senior" not in r[0].lower()]
        rates += rates_from_rows(special, rate_col=column_index(special, "Maturity Interest"), note="Special tenure")
    except ValueError:
        pass
    return rates
