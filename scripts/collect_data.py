from __future__ import annotations

from ukhpi.data_collection import DataCollection
from argparse import ArgumentParser


if __name__ == "__main__":
    data_collection = DataCollection()
    data_collection.collect_data()
