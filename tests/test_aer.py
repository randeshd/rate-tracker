import pytest

from scrapers.core.aer import aer_at_maturity
from scrapers.core.models import Rate, validate


def test_twelve_months_equals_nominal():
    assert aer_at_maturity(10, 12) == 10


def test_short_term_aer_is_higher_than_nominal():
    # 1 month at 12%: (1.01)^12 - 1
    assert aer_at_maturity(12, 1) == pytest.approx(12.6825, abs=1e-4)


def test_long_term_aer_is_lower_than_nominal():
    # 24 months at 10%: sqrt(1.2) - 1
    assert aer_at_maturity(10, 24) == pytest.approx(9.5445, abs=1e-4)


def test_validate_drops_long_tenures_and_sorts():
    out = validate([Rate(36, 9), Rate(12, 8), Rate(3, 7)])
    assert [r.tenure_months for r in out] == [3, 12]


def test_validate_rejects_implausible():
    with pytest.raises(ValueError):
        validate([Rate(12, 0.08)])


def test_day_count_terms_use_exact_days():
    r = Rate.for_days(400, 10.5, "Special FD")
    assert r.tenure_months == 13
    assert r.note == "400 days, Special FD"
    assert r.aer_pct == pytest.approx(10.45, abs=0.01)  # matches the AER DFCC publishes
