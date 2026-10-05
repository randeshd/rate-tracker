import re

from ..core.fetch import fetch
from ..core.models import Institution, Rate
from ..core.parse import soup_of, table_after, parse_pct

INSTITUTION = Institution(
    id="ndb",
    name="NDB Bank",
    type="bank",
    source_url="https://www.ndbbank.com/rates/interest-rates-on-deposits",
)

_TERM = re.compile(r"^(\d+)\s*(month|year|day)s?$", re.I)


def scrape() -> list[Rate]:
    soup = soup_of(fetch(INSTITUTION.source_url))
    rates = []
    term = None  # the term cell spans several payout rows
    for row in table_after(soup, r"Last Updated On"):
        if len(row) == 4:
            term, row = _TERM.match(row[0]), row[1:]
        if len(row) != 3 or term is None:
            continue
        payout, pct = row[0].lower(), parse_pct(row[1])
        if not pct or "maturity" not in payout:
            continue
        note = "NEOS FD (digital banking)" if "neos" in payout else ""
        n, unit = int(term.group(1)), term.group(2).lower()
        if unit == "day":
            rates.append(Rate.for_days(n, pct, note))
        else:
            rates.append(Rate(n * 12 if unit == "year" else n, pct, note))
    return rates
