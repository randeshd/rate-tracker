"""All institutions, in display order. Each module exposes INSTITUTION and scrape()."""
from importlib import import_module

MODULES = [
    # banks
    "peoples_bank", "hnb", "seylan", "ndb", "dfcc",
    # finance companies
    "lb_finance", "lolc_finance", "central_finance", "plc", "cdb", "singer_finance",
    "siyapatha", "hnb_finance", "mercantile", "vallibel",
]


def load(name: str):
    return import_module(f"scrapers.institutions.{name}")


def available() -> list[str]:
    out = []
    for name in MODULES:
        try:
            load(name)
            out.append(name)
        except ModuleNotFoundError:
            pass
    return out
