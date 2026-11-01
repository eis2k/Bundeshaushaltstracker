from bhtracker.model import BudgetRow, parse_amount


def test_parse_amount_tsd_to_euro():
    assert parse_amount("48207871", "tsd") == 48_207_871_000
    assert parse_amount("", "tsd") == 0


def test_parse_amount_eur_with_decimal_and_trailing_minus():
    assert parse_amount("1.088.350,00", "eur") == 1_088_350
    assert parse_amount("16,43-", "eur") == -16
    assert parse_amount("0,00", "eur") == 0


def test_parse_amount_rounds_half_up():
    assert parse_amount("2,50", "eur") == 3
    assert parse_amount("2,49", "eur") == 2


def test_budget_row_ids():
    r = BudgetRow(
        jahr=2025, stand="soll", art="A", epl="11", kap="1102", titel="63681",
        epl_text="Arbeit und Soziales", kap_text="Rentenversicherung",
        titel_text="Zuschuss", fkt="221", flex=False, soll=48_207_871_000,
    )
    assert r.id == "11-1102-63681"
    assert r.hg == "6"
    assert r.gruppe == "636"
    assert r.ist is None
    assert r.sv is False
