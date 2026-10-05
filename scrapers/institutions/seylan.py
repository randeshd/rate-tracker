from ..core.fetch import fetch
from ..core.models import Institution, Rate
from ..core.parse import soup_of, table_after, parse_tenure, parse_pct

INSTITUTION = Institution(
    id="seylan",
    name="Seylan Bank",
    type="bank",
    source_url="https://www.seylan.lk/interest-rates",
)


def scrape() -> list[Rate]:
    soup = soup_of(fetch(INSTITUTION.source_url))
    rates = []
    # columns: Interest Period | Interest Rate % p.a. | AER %
    for row in table_after(soup, r"Fixed Deposits - Interest Paid At Maturity"):
        tenure, pct = parse_tenure(row[0]), parse_pct(row[1]) if len(row) > 1 else None
        if tenure and pct:
            # rows marked ** need a larger minimum deposit (see footnote on the page)
            rates.append(Rate(tenure, pct, "Min Rs. 500,000" if "**" in row[0] else ""))
    try:  # the 1-month product is listed separately as Millennium'30
        for row in table_after(soup, r"Minimum Deposit - LKR 100,000"):
            tenure, pct = parse_tenure(row[0]), parse_pct(row[1]) if len(row) > 1 else None
            if tenure == 1 and pct:
                rates.append(Rate(1, pct, "Millennium'30 (min Rs. 100,000)"))
    except ValueError:
        pass
    return rates
