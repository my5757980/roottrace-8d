from app.numbers import find_untraceable

EVIDENCE = ["Customer measured 42.027-42.031 mm; 37 housings rejected.",
            "Coolant concentration shift (Δ -1.87), 31.8 h after the shift; Cpk -0.14."]


def test_traceable_number_passes_and_unknown_is_flagged():
    assert find_untraceable("Bore up to 42.031 mm", EVIDENCE) == []
    assert find_untraceable("Bore up to 42.0305 mm", EVIDENCE) == ["42.0305"]


def test_section_labels_and_small_integers_ignored():
    assert find_untraceable("D3 of the 8D uses 5W2H and 6M with 3 actions", EVIDENCE) == []


def test_rounded_value_is_traceable():
    assert find_untraceable("concentration dropped by 1.9", EVIDENCE) == []


def test_percentages_and_counts():
    assert find_untraceable("37 parts (100%) sorted", EVIDENCE) == []
    assert find_untraceable("45 parts sorted", EVIDENCE) == ["45"]


def test_years_ignored_and_ids_not_numbers():
    assert find_untraceable("Lot L261008-B in 2026", EVIDENCE) == []
