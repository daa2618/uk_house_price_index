import pandas as pd

from ukhpi.sparql import SparqlQuery


def test_build_query_for_region_includes_region_uri_and_year_range():
    sq = SparqlQuery()
    query = sq.build_query_for_region("united-kingdom", 2020, 2024)

    assert "http://landregistry.data.gov.uk/id/region/united-kingdom" in query
    assert "2020-01-01" in query
    assert "2024-12-01" in query
    assert "?refPeriodStart" in query


def test_build_query_for_region_normalises_region_slug():
    sq = SparqlQuery()
    query = sq.build_query_for_region("West Northamptonshire", 2023, 2023)
    assert "/region/west-northamptonshire>" in query


def test_make_data_from_results_with_empty_bindings_returns_typed_empty_frame():
    results = {"head": {"vars": ["averagePrice", "refPeriodStart"]}, "results": {"bindings": []}}
    df = SparqlQuery.make_data_from_results(results)

    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert "average_price" in df.columns
    assert "ref_period_start" in df.columns


def test_make_data_from_results_with_bindings_parses_dates_and_numerics():
    results = {
        "head": {"vars": ["averagePrice", "refPeriodStart"]},
        "results": {
            "bindings": [
                {
                    "averagePrice": {"value": "250000"},
                    "refPeriodStart": {"value": "2023-01-01"},
                },
                {
                    "averagePrice": {"value": "260000"},
                    "refPeriodStart": {"value": "2023-02-01"},
                },
            ]
        },
    }

    df = SparqlQuery.make_data_from_results(results)

    assert len(df) == 2
    assert pd.api.types.is_numeric_dtype(df["average_price"])
    assert pd.api.types.is_datetime64_any_dtype(df["ref_period_start"])
