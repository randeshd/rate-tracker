from ..core.fetch import fetch
from ..core.models import Institution, Rate
from ..core.parse import soup_of, table_after, parse_tenure, parse_pct

INSTITUTION = Institution(
    id="peoples_bank",
    name="People's Bank",
    type="bank",
    source_url="https://www.peoplesbank.lk/interest-rates/",
)


def _maturity_rates(rows, note=""):
    # columns: Period | At Maturity p.a. ("8.50% 8.50%(AER)") | Monthly p.a.
    out = []
    for row in rows:
        if len(row) < 2:
            continue
        tenure, pct = parse_tenure(row[0]), parse_pct(row[1])
        if tenure and pct:
            out.append(Rate(tenure, pct, note))
    return out


def scrape() -> list[Rate]:
    soup = soup_of(fetch(INSTITUTION.source_url))
    rates = _maturity_rates(table_after(soup, r"Fixed deposits \(Minimum deposit"))
    try:  # special product; may be withdrawn at any time
        rates += _maturity_rates(
            table_after(soup, r"People.s Wealth.{0,3} Fixed Deposit"),
            note="People's Wealth (min Rs. 250,000, new deposits)",
        )
    except ValueError:
        pass
    return rates
