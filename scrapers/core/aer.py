"""Annual Equivalent Rate for deposits that pay interest at maturity."""


def aer_at_maturity(nominal_pct: float, tenure_months: int) -> float:
    """AER (%) = (1 + r*t)^(1/t) - 1, with r the nominal annual rate and t the term in years."""
    r = nominal_pct / 100
    t = tenure_months / 12
    return round(((1 + r * t) ** (1 / t) - 1) * 100, 4)
