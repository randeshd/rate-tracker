from ..core.fetch import fetch
from ..core.models import Institution, Rate
from ..core.parse import soup_of, table_rows
from ..core.rows import rates_from_rows, column_index

INSTITUTION = Institution(
    id="mercantile",
    name="Mercantile Investments",
    type="finance",
    source_url="https://www.mi.com.lk/index.php/en/products-and-services/main-products/fixed-deposit",
)


def scrape() -> list[Rate]:
    soup = soup_of(fetch(INSTITUTION.source_url))
    candidates = []
    for table in soup.find_all("table"):
        rows = table_rows(table)
        try:
            candidates.append(rates_from_rows(rows, rate_col=column_index(rows, "Maturity")))
        except ValueError:
            continue
    candidates = [c for c in candidates if c]
    if not candidates:
        raise ValueError("fixed deposit rate table not found")
    # The page shows two unlabelled tables (general, then senior citizens with a bonus
    # on longer terms). The general one is the table with the lower rates.
    return min(candidates, key=lambda rates: sum(r.nominal_pct for r in rates))
