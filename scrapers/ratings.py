"""Credit ratings (run weekly). Writes data/ratings.json.

Two sources:
- Lanka Rating Agency's public ratings list: rating, outlook and date.
- Fitch Ratings Lanka: Fitch's own site does not allow automated access, so the Fitch
  rating is read from the statement each institution publishes on its own website.
  That gives the rating and usually the outlook, but not the rating date.

If a source fails, the previous entries from that source are kept and marked stale.

Usage: python -m scrapers.ratings
"""
import re
from datetime import datetime, timedelta, timezone

from . import registry
from .core import store
from .core.fetch import fetch
from .core.parse import soup_of, table_rows, clean

RATINGS_FILE = store.DATA_DIR / "ratings.json"
LRA_URL = "https://lra.com.lk/ratings/"
LRA = "Lanka Rating Agency"
FITCH = "Fitch Ratings Lanka"

# Legal names as they appear in Lanka Rating Agency's list
LRA_NAMES = {
    "peoples_bank": r"People.s Bank",
    "hnb": r"Hatton National Bank",
    "seylan": r"Seylan Bank",
    "ndb": r"National Development Bank",
    "dfcc": r"DFCC Bank",
    "pan_asia": r"Pan Asia Banking",
    "lb_finance": r"LB Finance",
    "lolc_finance": r"LOLC Finance",
    "central_finance": r"Central Finance",
    "plc": r"People.s Leasing",
    "cdb": r"Citizens Development Business Finance",
    "singer_finance": r"Singer Finance",
    "siyapatha": r"Siyapatha Finance",
    "hnb_finance": r"HNB Finance",
    "mercantile": r"Mercantile Investments",
    "vallibel": r"Vallibel Finance",
}

# Extra pages (besides the rates page) where an institution states its rating
DISCLOSURE_PAGES = {
    "peoples_bank": ["https://www.peoplesbank.lk/"],
    "lb_finance": ["https://www.lbfinance.com/"],
    "central_finance": ["https://www.cf.lk/"],
    "plc": ["https://www.plc.lk/"],
    "singer_finance": ["https://www.singerfinance.com/"],
    "mercantile": ["https://www.mi.com.lk/"],
}

# "A+(lka)", "A‑ (lka)", "BBB (Ika)" [sic]; hyphen variants are normalised to "-"
_FITCH_RATING = re.compile(r"(?<![A-Za-z])([A-D]{1,3})\s?([+\-‐-―−]?)\s*\(\s*[lI]ka\s*\)", re.I)
_OUTLOOK = re.compile(r"\b(stable|positive|negative|evolving)\b", re.I)


def lra_ratings() -> dict[str, dict]:
    """Latest entity rating per institution from Lanka Rating Agency's list (newest first)."""
    soup = soup_of(fetch(LRA_URL))
    out: dict[str, dict] = {}
    for table in soup.find_all("table"):
        for row in table_rows(table):
            # Entity | Sector | Rating Type | Dissemination Date | Action | LT | ST | Outlook | Watch
            if len(row) != 9 or row[2] != "Entity" or "withdraw" in row[4].lower():
                continue
            for inst_id, pattern in LRA_NAMES.items():
                if inst_id not in out and re.search(rf"(?<![A-Za-z]){pattern}(?! Holdings)", row[0], re.I):
                    try:
                        day = datetime.strptime(row[3], "%d-%b-%y").date().isoformat()
                    except ValueError:
                        day = ""
                    out[inst_id] = {
                        "agency": LRA,
                        "rating": row[5],
                        "outlook": row[7] if row[7] != "-" else "",
                        "date": day,
                        "source": "Lanka Rating Agency ratings list",
                        "source_url": LRA_URL,
                    }
    return out


def find_fitch_statement(text: str) -> dict | None:
    """Pull a Fitch national rating (and outlook, if stated nearby) out of page text."""
    best = None
    for m in _FITCH_RATING.finditer(text):
        window = text[max(0, m.start() - 120) : m.end() + 120]
        if "fitch" not in window.lower():
            continue
        sign = "-" if m.group(2) and m.group(2) != "+" else m.group(2)
        nearby = text[max(0, m.start() - 30) : m.end() + 40]
        outlook = _OUTLOOK.search(nearby)
        found = {"rating": f"{m.group(1).upper()}{sign}(lka)", "outlook": outlook.group(1).capitalize() if outlook else ""}
        if found["outlook"]:
            return found  # prefer a statement that also gives the outlook
        best = best or found
    return best


def fitch_rating(inst) -> dict | None:
    for url in [inst.source_url] + DISCLOSURE_PAGES.get(inst.id, []):
        found = find_fitch_statement(clean(soup_of(fetch(url)).get_text(" ")))
        if found:
            return {
                "agency": FITCH,
                **found,
                "date": "",
                "source": "As stated on the institution's website",
                "source_url": url,
            }
    return None


def run() -> None:
    now = datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(timespec="seconds")
    previous = store.load_json(RATINGS_FILE, {"institutions": {}})["institutions"]

    def kept(inst_id: str, agency: str) -> list[dict]:
        return [{**r, "stale": True} for r in previous.get(inst_id, []) if r["agency"] == agency]

    try:
        lra, lra_ok = lra_ratings(), True
    except Exception as e:
        lra, lra_ok = {}, False
        print(f"FAILED Lanka Rating Agency list: {type(e).__name__}: {e}")

    result = {}
    for name in registry.MODULES:
        inst = registry.load(name).INSTITUTION
        ratings = []
        try:
            found = fitch_rating(inst)
            ratings += [{**found, "checked_at": now}] if found else []
        except Exception as e:
            ratings += kept(inst.id, FITCH)
            print(f"FAILED {inst.id} website: {type(e).__name__}: {e}")
        if lra_ok:
            ratings += [{**lra[inst.id], "checked_at": now}] if inst.id in lra else []
        else:
            ratings += kept(inst.id, LRA)
        result[inst.id] = ratings
        print(f"{inst.id}: " + ("; ".join(f"{r['agency']} {r['rating']} {r['outlook']} {r['date']}".strip() for r in ratings) or "no rating found"))
    store.save_json(RATINGS_FILE, {"updated_at": now, "institutions": result})


if __name__ == "__main__":
    run()
