"""Small parsing helpers shared by scrapers."""
import re

from bs4 import BeautifulSoup

_WORDS = {"one": 1, "two": 2, "three": 3, "six": 6, "twelve": 12}


def soup_of(html: str | bytes) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def table_rows(table) -> list[list[str]]:
    return [[clean(c.get_text(" ")) for c in tr.find_all(["th", "td"])] for tr in table.find_all("tr")]


def all_tables(html: str | bytes) -> list[list[list[str]]]:
    return [table_rows(t) for t in soup_of(html).find_all("table")]


def parse_tenure(text: str) -> int | None:
    """'01 Month' -> 1, '2 Years' -> 24, '1 1/2 years' -> 18, '400 Days' -> 13. None if not a tenure."""
    t = clean(text).lower()
    for word, n in _WORDS.items():
        t = re.sub(rf"\b{word}\b", str(n), t)
    m = re.search(r"(\d+)\s*(?:-|\s)?\s*(months?|mths?|m\b|years?|yrs?|y\b|days?)", t)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    if unit.startswith("d"):
        return round(n / 30.4) or None
    if unit.startswith("y"):
        months = n * 12
        if re.search(r"1\s*/\s*2|½|\.5", t):
            months += 6
        return months
    return n


def parse_pct(text: str) -> float | None:
    """First number in the text, e.g. '8.50%' -> 8.5. None for '-' or blanks."""
    m = re.search(r"\d+(?:\.\d+)?", clean(text))
    return float(m.group()) if m else None


def table_after(soup: BeautifulSoup, pattern: str) -> list[list[str]]:
    """Rows of the table containing (or else first following) text matching the regex pattern."""
    node = soup.find(string=re.compile(pattern, re.I))
    if node is None:
        raise ValueError(f"heading not found: {pattern}")
    table = node.find_parent("table") or node.find_next("table")
    if table is None:
        raise ValueError(f"no table after: {pattern}")
    return table_rows(table)
