import pandas as pd

import ukhpi.hpi as hpi_module
from ukhpi.hpi import HousePriceIndex, HousePriceIndexPlots


def _fake_results():
    return {
        "head": {"vars": ["averagePrice", "refPeriodStart"]},
        "results": {
            "bindings": [
                {
                    "averagePrice": {"value": "250000"},
                    "refPeriodStart": {"value": "2023-01-01"},
                },
            ]
        },
    }


def test_house_price_index_init_does_not_hit_network(monkeypatch):
    """Constructor must be lazy — no SPARQL fetch on instantiation."""
    calls = {"n": 0}

    def boom(*a, **kw):
        calls["n"] += 1
        raise AssertionError("SPARQL endpoint was called from __init__")

    monkeypatch.setattr(hpi_module.sparqlquery, "fetch_sparql_query", boom)

    HousePriceIndex()
    assert calls["n"] == 0


def test_fetch_hpi_returns_dataframe_via_monkeypatched_sparql(monkeypatch, tmp_path):
    monkeypatch.setattr(
        hpi_module.sparqlquery, "fetch_sparql_query", lambda q: _fake_results()
    )

    hpi = HousePriceIndex()
    hpi._data_path = tmp_path

    df = hpi.fetch_hpi(2023, 2023, "united-kingdom")

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "ref_period_start" in df.columns


def test_house_price_index_plots_constants_are_class_level():
    """PAYMENT/OCCUPANT/BUILD types should be class attrs, not __init__-set."""
    assert HousePriceIndexPlots.PAYMENT_TYPES == ["cash", "mortgage"]
    assert "first time buyer" in HousePriceIndexPlots.OCCUPANT_TYPES
    assert "new build" in HousePriceIndexPlots.BUILD_TYPES


def test_house_price_index_plots_init_does_not_hit_network(monkeypatch):
    monkeypatch.setattr(
        hpi_module.sparqlquery,
        "fetch_sparql_query",
        lambda q: (_ for _ in ()).throw(AssertionError("SPARQL called from __init__")),
    )

    p = HousePriceIndexPlots(2023, 2023, "england")
    assert p._start_year == 2023
    assert p._region == "england"
