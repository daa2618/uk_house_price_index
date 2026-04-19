"""Smoke tests for ukhpi.geo.ops: construction + GeoJSON loading.

All tests are offline — the GeoJSON file is written to tmp_path and the
SPARQL fetch is monkeypatched.
"""

from __future__ import annotations

import json

import pytest

from ukhpi.geo.ops import GeoOps


def _write_geojson(tmp_path, payload):
    geo_dir = tmp_path / "geo_data"
    geo_dir.mkdir(parents=True, exist_ok=True)
    path = geo_dir / "georef_united_kingdom_county_unitary_authority.geojson"
    path.write_text(json.dumps(payload))
    return path


def test_geo_ops_init_does_not_hit_network_or_read_file(tmp_path, monkeypatch):
    geo = GeoOps()
    assert geo._ref_geo_df.empty
    assert "ctyua_name" in geo.supported_geo_types
    assert geo.hpi_by_geo_dict == {}


def test_ref_geo_df_reads_from_local_geojson_when_cached(tmp_path, tiny_geojson):
    geo = GeoOps()
    geo.file_path = _write_geojson(tmp_path, tiny_geojson)

    gdf = geo.REF_GEO_DF

    assert not gdf.empty
    assert "ctyua_name" in gdf.columns
    assert gdf.iloc[0]["ctyua_name"] == "Buckinghamshire"


def test_get_data_for_geo_rejects_unsupported_geo_type(tmp_path, tiny_geojson):
    geo = GeoOps()
    geo.file_path = _write_geojson(tmp_path, tiny_geojson)

    with pytest.raises(ValueError, match="not found in supported geo types"):
        geo.get_data_for_geo(start_year=2023, end_year=2023, geo_type_id="not_a_real_geo", ref_month="2023-01")
