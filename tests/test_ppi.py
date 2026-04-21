"""Tests for ukhpi.core.ppi and the postcode SPARQL query builder.

All tests are offline — SPARQL calls are monkeypatched.
"""

from __future__ import annotations

import pandas as pd

import ukhpi.core.ppi as ppi_module
from ukhpi.core.ppi import PricePaidData, PricePaidDataPlots
from ukhpi.core.sparql import SparqlQuery


def test_build_query_for_postcode_uppercases_and_includes_postcode():
    sq = SparqlQuery()
    query = sq.build_query_for_postcode("hp20 1aa")

    assert '"HP20 1AA"^^xsd:string' in query
    assert "?transx" in query
    assert "lrppi:pricePaid" in query
    assert "lrppi:transactionDate" in query


def test_price_paid_data_init_does_not_hit_network(monkeypatch):
    """Constructor must be lazy — no SPARQL fetch on instantiation."""

    def boom(*a, **kw):
        raise AssertionError("SPARQL endpoint was called from __init__")

    monkeypatch.setattr(ppi_module.sparq, "get_price_paid_data_for_postcode", boom)

    ppd = PricePaidData("HP20 1AA")
    assert ppd._postcode == "HP20 1AA"


def test_clean_df_coerces_numeric_and_date_columns(monkeypatch):
    raw = pd.DataFrame(
        {
            "paon": ["12", "14"],
            "saon": ["", ""],
            "street": ["High Street", "High Street"],
            "town": ["Aylesbury", "Aylesbury"],
            "postcode": ["HP20 1AA", "HP20 1AA"],
            "amount": ["250000", "310000"],
            "date": ["2023-01-15", "2023-06-22"],
            "category": [
                "Standard price paid transaction",
                "Standard price paid transaction",
            ],
        }
    )

    monkeypatch.setattr(ppi_module.sparq, "get_price_paid_data_for_postcode", lambda _pc: raw.copy())

    ppd = PricePaidData("HP20 1AA")
    cleaned = ppd.clean_df()

    assert pd.api.types.is_numeric_dtype(cleaned["amount"])
    assert pd.api.types.is_datetime64_any_dtype(cleaned["date"])
    assert "address" in cleaned.columns
    assert cleaned["address"].iloc[0] == "12, High Street, HP20 1AA"


def test_clean_df_includes_saon_in_address_when_present(monkeypatch):
    """Flat number should be prepended to the address key so adjacent flats don't collide."""
    raw = pd.DataFrame(
        {
            "paon": ["10", "10"],
            "saon": ["FLAT 1", "FLAT 2"],
            "street": ["High Street", "High Street"],
            "postcode": ["HP20 1AA", "HP20 1AA"],
            "amount": ["250000", "310000"],
            "date": ["2023-01-15", "2023-06-22"],
            "category": [
                "Standard price paid transaction",
                "Standard price paid transaction",
            ],
        }
    )
    monkeypatch.setattr(ppi_module.sparq, "get_price_paid_data_for_postcode", lambda _pc: raw.copy())

    cleaned = PricePaidData("HP20 1AA").clean_df()

    assert cleaned["address"].iloc[0] == "10 FLAT 1, High Street, HP20 1AA"
    assert cleaned["address"].iloc[1] == "10 FLAT 2, High Street, HP20 1AA"
    assert cleaned["address"].nunique() == 2


def test_clean_df_filters_non_add_records_and_dedupes_transaction_id(monkeypatch):
    """Rows superseded by Change/Delete must be dropped; duplicate transaction ids collapsed."""
    raw = pd.DataFrame(
        {
            "paon": ["12", "12", "14"],
            "saon": ["", "", ""],
            "street": ["High Street", "High Street", "High Street"],
            "postcode": ["HP20 1AA", "HP20 1AA", "HP20 1AA"],
            "amount": ["250000", "260000", "310000"],
            "date": ["2023-01-15", "2023-02-01", "2023-06-22"],
            "category": [
                "Standard price paid transaction",
                "Standard price paid transaction",
                "Standard price paid transaction",
            ],
            "record_status": [
                "http://landregistry.data.gov.uk/def/ppi/add",
                "http://landregistry.data.gov.uk/def/ppi/delete",
                "Add",
            ],
            "transaction_id": ["tx-1", "tx-1", "tx-2"],
        }
    )
    monkeypatch.setattr(ppi_module.sparq, "get_price_paid_data_for_postcode", lambda _pc: raw.copy())

    cleaned = PricePaidData("HP20 1AA").clean_df()

    assert len(cleaned) == 2
    assert set(cleaned["transaction_id"]) == {"tx-1", "tx-2"}
    assert not any("delete" in str(s).lower() for s in cleaned["record_status"])


def test_calculate_appreciated_prices_returns_cagr_and_skips_same_day(monkeypatch):
    """CAGR must match the compound-growth formula; same-day second sales must not divide by zero."""
    raw = pd.DataFrame(
        {
            "paon": ["10", "10", "20", "20"],
            "saon": ["", "", "", ""],
            "street": ["High Street", "High Street", "Low Road", "Low Road"],
            "postcode": ["HP20 1AA"] * 4,
            "amount": ["200000", "400000", "500000", "510000"],
            "date": ["2014-01-01", "2024-01-01", "2023-05-01", "2023-05-01"],
            "category": ["Standard price paid transaction"] * 4,
        }
    )
    monkeypatch.setattr(ppi_module.sparq, "get_price_paid_data_for_postcode", lambda _pc: raw.copy())

    result = PricePaidData("HP20 1AA").calculate_appreciated_prices()

    # Same-day pair (20, Low Road) must be skipped, not raise.
    assert len(result) == 1
    row = result.iloc[0]
    assert row["address"] == "10, High Street, HP20 1AA"
    # 2x over 10 years → ~7.18% CAGR
    assert 7.0 < row["cagr_pct"] < 7.4
    assert row["price_change"] == 200000
    assert {"first_date", "last_date", "hold_years", "p_start", "p_end"} <= set(result.columns)


def test_new_plot_methods_return_figures_with_traces(monkeypatch):
    """V1-V5 smoke test: each plot method must return a Figure with >=1 trace for non-empty input."""
    raw = pd.DataFrame(
        {
            "paon": ["10", "10", "20", "30"],
            "saon": ["", "", "", ""],
            "street": ["High Street"] * 4,
            "postcode": ["HP20 1AA"] * 4,
            "amount": ["200000", "260000", "500000", "310000"],
            "date": ["2020-01-15", "2024-01-15", "2022-05-01", "2023-06-22"],
            "category": ["Standard price paid transaction"] * 4,
            "property_type": ["Terraced", "Terraced", "Detached", "Semi-detached"],
            "estate_type": ["Freehold", "Freehold", "Freehold", "Leasehold"],
        }
    )
    monkeypatch.setattr(ppi_module.sparq, "get_price_paid_data_for_postcode", lambda _pc: raw.copy())

    plots = PricePaidDataPlots("HP20 1AA")
    for name in (
        "plot_price_distribution",
        "plot_price_timeline",
        "plot_property_type_medians",
        "plot_tenure_mix",
        "plot_monthly_volume",
    ):
        fig = getattr(plots, name)()
        assert fig is not None, f"{name} returned None"
        assert len(fig.data) >= 1, f"{name} produced no traces"


def test_clean_df_falls_back_to_string_paon_when_not_numeric(monkeypatch):
    """The paon coercion path — non-numeric paons must survive without error."""
    raw = pd.DataFrame(
        {
            "paon": ["FLAT A", "FLAT B"],
            "saon": ["", ""],
            "street": ["High Street", "High Street"],
            "town": ["Aylesbury", "Aylesbury"],
            "postcode": ["HP20 1AA", "HP20 1AA"],
            "amount": ["250000", "310000"],
            "date": ["2023-01-15", "2023-06-22"],
            "category": [
                "Standard price paid transaction",
                "Standard price paid transaction",
            ],
        }
    )

    monkeypatch.setattr(ppi_module.sparq, "get_price_paid_data_for_postcode", lambda _pc: raw.copy())

    ppd = PricePaidData("HP20 1AA")
    cleaned = ppd.clean_df()

    assert cleaned["paon"].dtype == object
    assert cleaned["paon"].iloc[0] == "FLAT A"
