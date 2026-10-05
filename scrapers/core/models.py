"""Common data format shared by every scraper."""
from dataclasses import dataclass, field, asdict

from .aer import aer_at_maturity, days_to_months

STANDARD_TENURES = [1, 3, 6, 12, 13, 18, 24]
MAX_TENURE = 24


@dataclass
class Rate:
    tenure_months: int
    nominal_pct: float  # annual rate, interest paid at maturity
    aer_pct: float = field(init=False)
    note: str = ""  # empty for the standard FD; otherwise the name/conditions of a special offer

    days: int | None = None  # set when the term is quoted in days (e.g. a 400-day FD)

    def __post_init__(self):
        exact_months = days_to_months(self.days) if self.days else self.tenure_months
        self.aer_pct = aer_at_maturity(self.nominal_pct, exact_months)

    @classmethod
    def for_days(cls, days: int, nominal_pct: float, note: str = "") -> "Rate":
        """A day-count term, filed under the nearest whole month."""
        label = f"{days} days" + (f", {note}" if note else "")
        return cls(max(1, round(days_to_months(days))), nominal_pct, label, days)


@dataclass
class Institution:
    id: str
    name: str
    type: str  # "bank" or "finance"
    source_url: str


def validate(rates: list[Rate]) -> list[Rate]:
    """Drop tenures beyond 24 months, reject implausible values, sort by tenure.

    One rate per (tenure, note): a special offer can sit alongside the standard rate.
    """
    if not rates:
        raise ValueError("no rates found")
    seen = {}
    for r in rates:
        if not 1 <= r.tenure_months <= MAX_TENURE:
            continue
        if not 1.0 <= r.nominal_pct <= 40.0:
            raise ValueError(f"implausible rate {r.nominal_pct}% for {r.tenure_months}m")
        seen[(r.tenure_months, r.note)] = r
    if not seen:
        raise ValueError("no rates within 1-24 months")
    return [seen[k] for k in sorted(seen)]


def to_dicts(rates: list[Rate]) -> list[dict]:
    return [asdict(r) for r in rates]
