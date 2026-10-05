"""CBSL maximum deposit rates for finance companies (reference only).

Finance Business Act Directions No. 01 of 2025, as amended by No. 01 of 2026: the maximum
annual nominal rate for deposits paying interest at maturity is a Treasury bill yield plus
a margin, reviewed quarterly using the simple average of the last four primary auctions of
the previous quarter. It covers tenures from one month to less than two years and applies
to licensed finance companies, not banks.

T-bill yields are read from CBSL's Weekly Economic Indicators (published on Fridays,
covering that week's auction).

The margins come from the directions themselves, which CBSL publishes as scanned PDFs, so
they are written into BANDS below. To catch a future amendment, every run also checks
CBSL's list of directions: a deposit-rate direction that is not in KNOWN_DIRECTIONS is
recorded in data/cbsl.json (the web page then shows a warning) and `--alert` exits with an
error so the GitHub Actions run fails and sends a notification.

Usage: python -m scrapers.cbsl [--alert]
"""
import io
import re
import sys
from urllib.parse import urljoin
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

import pdfplumber
import requests

from .core import store
from .core.fetch import fetch
from .core.parse import soup_of, clean

DIRECTION_URL = "https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/laws/cdg/snbfi_finance_business_act_directions_no_1_of_2026_e.pdf"
WEI_URL = "https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/statistics/wei/WEI_{:%Y%m%d}_e{}.pdf"
CBSL_FILE = store.DATA_DIR / "cbsl.json"
DIRECTIONS_LIST_URL = "https://www.cbsl.gov.lk/en/laws/directions-circulars-guidelines-for-non-banks"

# Deposit-rate directions already reflected in BANDS (file names on CBSL's site)
KNOWN_DIRECTIONS = {
    "snbfi_finance_business_act_directions_no_1_of_2025_e.pdf",
    "snbfi_finance_business_act_directions_no_1_of_2026_e.pdf",
}

# (from months, up to but excluding months, T-bill tenor in days, margin in % points)
BANDS = [
    (1, 3, 91, 1.10),
    (3, 6, 182, 1.25),
    (6, 12, 364, 1.50),
    (12, 24, 364, 3.00),
]
AUCTIONS = 4


def _round2(value: float) -> float:
    return float(Decimal(str(round(value, 6))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def previous_quarter(today: date) -> tuple[str, date]:
    """Label and last day of the quarter before the one containing today."""
    first_month = 3 * ((today.month - 1) // 3) + 1
    end = date(today.year, first_month, 1) - timedelta(days=1)
    return f"{end.year}-Q{(end.month - 1) // 3 + 1}", end


def _yields(pdf_bytes: bytes) -> dict[int, float]:
    """This week's primary market T-bill yields from a Weekly Economic Indicators PDF."""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages[:10])
    start = text.find("Treasury Bill Yields (Primary Market)")
    if start < 0:
        raise ValueError("T-bill yields section not found")
    out = {}
    for tenor in (91, 182, 364):
        # row: "<tenor> Day <year ago> <last week> <this week>"
        m = re.search(rf"{tenor}\s*Day\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", text[start : start + 400])
        if not m:
            raise ValueError(f"{tenor}-day yield not found")
        out[tenor] = float(m.group(3))
    return out


def _weekly_report(friday: date) -> bytes | None:
    for suffix in ("", "_r"):  # revised issues carry an _r suffix
        try:
            return fetch(WEI_URL.format(friday, suffix))
        except requests.HTTPError as e:
            if e.response is None or e.response.status_code != 404:
                raise
    return None


def compute(today: date) -> dict:
    quarter, quarter_end = previous_quarter(today)
    # Auctions are held mid-week; the Friday report covers that week's auction.
    friday = quarter_end + timedelta(days=(4 - quarter_end.weekday()) % 7)
    if friday - timedelta(days=4) > quarter_end:
        friday -= timedelta(days=7)
    weeks = []
    for _ in range(AUCTIONS + 4):  # allow for weeks without a report
        if friday <= today:
            pdf = _weekly_report(friday)
            if pdf:
                weeks.append({"report_date": friday.isoformat(), **{str(k): v for k, v in _yields(pdf).items()}})
        if len(weeks) == AUCTIONS:
            break
        friday -= timedelta(days=7)
    if len(weeks) < AUCTIONS:
        raise ValueError(f"only {len(weeks)} weekly reports found for {quarter}")
    average = {t: round(sum(w[str(t)] for w in weeks) / len(weeks), 4) for t in (91, 182, 364)}
    return {
        "based_on_quarter": quarter,
        "applies_to": "finance",
        "source_url": DIRECTION_URL,
        "tbill_average": {str(k): v for k, v in average.items()},
        "weeks": weeks,
        "bands": [
            {"from_months": lo, "to_months": hi, "tbill_days": t, "margin": m, "max_nominal_pct": _round2(average[t] + m)}
            for lo, hi, t, m in BANDS
        ],
    }


def unreviewed_directions() -> list[dict]:
    """Deposit-rate directions on CBSL's list that BANDS does not account for yet."""
    soup = soup_of(fetch(DIRECTIONS_LIST_URL))
    found = {}
    for link in soup.find_all("a", href=True):
        title = clean(link.get_text())
        if not re.search(r"interest rates? on deposits", title, re.I):
            continue
        url = urljoin(DIRECTIONS_LIST_URL, link["href"])
        if url.rsplit("/", 1)[-1] not in KNOWN_DIRECTIONS:
            found[url] = {"title": title, "url": url}
    return list(found.values())


def run(alert: bool = False) -> None:
    now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    current = store.load_json(CBSL_FILE, {})
    quarter, _ = previous_quarter(now.date())
    if current.get("based_on_quarter") == quarter and not current.get("stale"):
        result = current
        print(f"CBSL ceiling already up to date ({quarter})")
    else:
        try:
            result = compute(now.date())
            result["updated_at"] = now.isoformat(timespec="seconds")
            result["stale"] = False
            print("CBSL ceiling:", ", ".join(f"{b['from_months']}-{b['to_months']}m={b['max_nominal_pct']}" for b in result["bands"]))
        except Exception as e:  # keep the last good figures
            if not current:
                raise
            result = {**current, "stale": True, "error": f"{type(e).__name__}: {e}"[:300]}
            print("CBSL ceiling FAILED, keeping previous:", result["error"])

    try:
        result["unreviewed_directions"] = unreviewed_directions()
        result["directions_checked_at"] = now.isoformat(timespec="seconds")
    except Exception as e:
        print(f"Could not check CBSL directions list: {type(e).__name__}: {e}")
    store.save_json(CBSL_FILE, result)

    pending = result.get("unreviewed_directions", [])
    for d in pending:
        print(f"NEW CBSL DIRECTION, ceiling margins need review: {d['title']} {d['url']}")
    if alert and pending:
        sys.exit(1)


if __name__ == "__main__":
    run(alert="--alert" in sys.argv)
