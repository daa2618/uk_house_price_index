"""Smoke tests for ukhpi.postcode_lookups: import + callable resolution.

These confirm the helper_tools dependency has been fully removed. They do NOT
hit the network — heavy entry points are only referenced, not invoked.
"""

import importlib


def test_helper_imports_without_helper_tools():
    mod = importlib.import_module("ukhpi.postcode_lookups.helper")
    assert callable(mod.extract_from_url_and_create_sqlite_db)
    assert callable(mod.query_sqlite)


def test_aylesbury_postcodes_imports_without_helper_tools():
    mod = importlib.import_module("ukhpi.postcode_lookups.aylesbury_postcodes")
    assert callable(mod.make_aylesbury_postcodes)
    assert callable(mod.load_aylesbury_postcodes)


def test_aylesbury_ppi_imports_without_helper_tools():
    mod = importlib.import_module("ukhpi.postcode_lookups.aylesbury_ppi")
    assert callable(mod.extract_all_aylesbury_price_paid_data)
    assert callable(mod.make_db_of_results)
