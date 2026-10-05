from scrapers.ratings import find_fitch_statement


def test_rating_with_outlook():
    assert find_fitch_statement("Fitch Rating :'A+(lka)'; Outlook Stable National") == {"rating": "A+(lka)", "outlook": "Stable"}


def test_non_breaking_hyphen_and_no_outlook():
    assert find_fitch_statement("Security Measures A‑ (lka) Fitch Rating - National") == {"rating": "A-(lka)", "outlook": ""}


def test_misspelt_suffix():
    assert find_fitch_statement("PB232PQ BBB (Ika), Outlook Stable – Fitch Ratings Lanka Ltd.") == {"rating": "BBB(lka)", "outlook": "Stable"}


def test_ignores_ratings_not_attributed_to_fitch():
    assert find_fitch_statement("rated A(lka) by someone else entirely") is None
