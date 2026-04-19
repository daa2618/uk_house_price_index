"""Tests for ukhpi.core.ppi and the postcode SPARQL query builder.

All tests are offline — SPARQL calls are monkeypatched.
"""

from __future__ import annotations

import pandas as pd

import ukhpi.core.ppi as ppi_module
from ukhpi.core.ppi import PricePaidData
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
