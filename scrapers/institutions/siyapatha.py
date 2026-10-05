import re

from ..core.fetch import fetch
from ..core.models import Institution, Rate
from ..core.parse import soup_of, clean
from ..core.rows import rates_from_rows

INSTITUTION = Institution(
    id="siyapatha",
    name="Siyapatha Finance",
    type="finance",
    source_url="https://www.siyapatha.lk/fixed-deposits/",
)


def scrape() -> list[Rate]:
    soup = soup_of(fetch(INSTITUTION.source_url))
    heading = soup.find("h5", string=re.compile(r"Fixed Deposits for General Public", re.I))
    if heading is None:
        raise ValueError("general public rates section not found")
    # The "table" is built from div rows: Period | Maturity | A.E.R | Monthly | A.E.R
    rows = [
        [clean(col.get_text()) for col in row.find_all("div", class_="col")]
        for row in heading.parent.select("div.row div.row")
    ]
    return rates_from_rows(rows, rate_col=1)
