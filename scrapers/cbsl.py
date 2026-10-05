"""CBSL maximum deposit rates for finance companies (reference only).

Finance Business Act Directions No. 01 of 2025: the maximum annual nominal rate for
deposits paying interest at maturity is a Treasury bill yield plus a margin, reviewed
quarterly using the simple average of the last four primary auctions of the previous
quarter. The rule applies to licensed finance companies, not banks.

T-bill yields are read from CBSL's Weekly Economic Indicators (published on Fridays,
covering that week's auction), so the result is a close approximation of the official figure.

Usage: python -m scrapers.cbsl
"""
import io
import re
from datetime import date, datetime, timedelta, timezone

import pdfplumber
import requests

from .core import store
from .core.fetch import fetch

DIRECTION_URL = "https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/laws/cdg/snbfi_finance_business_act_directions_no_1_of_2025_e.pdf"
WEI_URL = "https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/statistics/wei/WEI_{:%Y%m%d}_e{}.pdf"
CBSL_FILE = store.DATA_DIR / "cbsl.json"

# (from months, up to but excluding months, T-bill tenor in days, margin in % points)
BANDS = [
    (1, 3, 91, 0.10),
    (3, 6, 182, 0.25),
    (6, 12, 364, 0.50),
    (12, 24, 364, 2.00),
    (24, 36, 364, 2.75),
]
AUCTIONS = 4


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
            {"from_months": lo, "to_months": hi, "tbill_days": t, "margin": m, "max_nominal_pct": round(average[t] + m, 2)}
            for lo, hi, t, m in BANDS
        ],
    }


def run() -> None:
    now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    current = store.load_json(CBSL_FILE, {})
    quarter, _ = previous_quarter(now.date())
    if current.get("based_on_quarter") == quarter and not current.get("stale"):
        print(f"CBSL ceiling already up to date ({quarter})")
        return
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
    store.save_json(CBSL_FILE, result)


if __name__ == "__main__":
    run()
