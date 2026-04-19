from pathlib import Path

import pytest

from ukhpi.core.collection import DEFAULT_DATA_PATH, build_parser, main


def test_parser_defaults():
    args = build_parser().parse_args([])
    assert args.start_year == 1990
    assert args.end_year == 2025
    assert args.data_path == DEFAULT_DATA_PATH


def test_parser_accepts_custom_args(tmp_path):
    args = build_parser().parse_args(
        [
            "--start-year",
            "2020",
            "--end-year",
            "2023",
            "--data-path",
            str(tmp_path),
        ]
    )
    assert args.start_year == 2020
    assert args.end_year == 2023
    assert args.data_path == tmp_path


def test_parser_help_exits_cleanly(capsys):
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--data-path" in out
    assert "--start-year" in out


def test_main_instantiates_data_collection(monkeypatch, tmp_path):
    """Regression: previously `DataCollection()` was called with no args and raised TypeError."""
    calls = {}

    class StubCollection:
        def __init__(self, data_path, start_year, end_year):
            calls["data_path"] = Path(data_path)
            calls["start_year"] = start_year
            calls["end_year"] = end_year

        def collect_data(self):
            calls["collected"] = True
            return None

    monkeypatch.setattr("ukhpi.core.collection.DataCollection", StubCollection)

    main(["--data-path", str(tmp_path), "--start-year", "2022", "--end-year", "2022"])

    assert calls["data_path"] == tmp_path
    assert calls["start_year"] == 2022
    assert calls["end_year"] == 2022
    assert calls["collected"] is True
