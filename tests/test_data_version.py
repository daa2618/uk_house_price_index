import datetime

from ukhpi.io.versioning import FileVersion


def test_make_file_name_appends_today_and_extension(tmp_path):
    fv = FileVersion(base_path=tmp_path, file_name="hpi", extension="csv")
    name = fv.make_file_name()

    today = datetime.datetime.now().strftime("%m%d%Y")
    assert name == f"hpi_{today}.csv"


def test_fetch_dates_round_trip_with_existing_file(tmp_path):
    fv = FileVersion(base_path=tmp_path, file_name="hpi", extension="csv")
    today = datetime.datetime.now()
    today_floor = datetime.datetime(today.year, today.month, today.day)
    fname = fv.make_file_name()
    (tmp_path / fname).write_text("col\n1\n")

    dates = fv._fetch_dates_from_file_names()
    assert dates == [today_floor]


def test_latest_file_path_returns_newest(tmp_path):
    fv = FileVersion(base_path=tmp_path, file_name="hpi", extension="csv")

    older = "hpi_01012023.csv"
    newer = "hpi_06152024.csv"
    (tmp_path / older).write_text("x\n")
    (tmp_path / newer).write_text("x\n")

    latest = fv.latest_file_path
    assert latest is not None
    assert latest.name == newer


def test_latest_file_path_returns_none_when_empty(tmp_path):
    fv = FileVersion(base_path=tmp_path, file_name="hpi", extension="csv")
    assert fv.latest_file_path is None
