import collections
import datetime
from utils import db_interface
import math
import pprint
import sqlite3
import sys

# Testing Testing
import numpy as np
import pandas as pd

import logging


def load_ratings_dataframe(rows):
    column_names = rows[0].keys()
    ratings = pd.DataFrame(rows, columns=column_names).astype({'date': 'datetime64'})
    return ratings


def load_items_dataframe(schedule_rows):
    types = {'start': 'datetime64'}
    column_names = schedule_rows[0].keys()
    items = pd.DataFrame(schedule_rows, columns=column_names).astype(types)

    # Convert everything to proper data types
    completion_dict = {'NaN': None, 0: False, 1: True}
    items['completed'] = items['completed'].map(completion_dict)

    return items


def load_data(database, start_date=None, end_date=None):
    with sqlite3.connect(database) as con:
        con.row_factory = sqlite3.Row
        ratings_rows = db_interface.get_ratings_for_stats(con)
        schedule_rows = db_interface.get_schedule_for_stats(con, start_date, end_date)
    if ratings_rows:
        ratings = load_ratings_dataframe(ratings_rows)
    else:
        ratings = None
    if schedule_rows:
        items = load_items_dataframe(schedule_rows)
    else:
        items = None

    return ratings, items


def main():
    if len(sys.argv) > 1:
        dbf = f"tests/{sys.argv[1]}"
    else:
        dbf = "tests/randy.db"

    ratings, items = load_data(dbf)
    print(ratings.value_counts())
    print(items)


if __name__ == "__main__":
    main()
