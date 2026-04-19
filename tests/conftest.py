"""Shared pytest fixtures for the ukhpi test suite."""

from __future__ import annotations

import pytest


@pytest.fixture
def fake_sparql_bindings():
    """A minimal SPARQL JSON response with two HPI rows."""
    return {
        "head": {"vars": ["averagePrice", "refPeriodStart", "refRegion"]},
        "results": {
            "bindings": [
                {
                    "averagePrice": {"value": "250000"},
                    "refPeriodStart": {"value": "2023-01-01"},
                    "refRegion": {"value": "http://landregistry.data.gov.uk/id/region/england"},
                },
                {
                    "averagePrice": {"value": "260000"},
                    "refPeriodStart": {"value": "2023-02-01"},
                    "refRegion": {"value": "http://landregistry.data.gov.uk/id/region/england"},
                },
            ]
        },
    }


@pytest.fixture
def tiny_geojson():
    """A tiny GeoJSON FeatureCollection with one polygon per supported geo type."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "ctry_name": "England",
                    "rgn_name": "South East",
                    "ctyua_name": "Buckinghamshire",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
            }
        ],
    }
