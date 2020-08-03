""" Initialize Day Builder's database and tables """

import sqlite3
from datetime import datetime, timedelta
import os

# Create database

def init_db(db):
    """
    Open and close the specified file 
    to make sure it exists.
    """
    path = os.path.dirname(db)
    if not os.path.exists(path):
        os.makedirs(path)
    newdb = open(db, "w+")
    newdb.close()


# Create Items table
def create_items_table(db):
    sql = """CREATE TABLE IF NOT EXISTS items (
                item_id integer PRIMARY KEY,
                item_type integer NOT NULL,
                item_name text NOT NULL
                ); """
    con = sqlite3.connect(db)
    con.execute(sql)
    con.close()

# Create Tags table
def create_tags_table(db):
    sql = """CREATE TABLE IF NOT EXISTS tags (
                tag_id integer PRIMARY KEY,
                tag_name text NOT NULL
                );"""
    con = sqlite3.connect(db)
    con.execute(sql)
    con.close()

# Create Tag_Map table
def create_tag_map_table(db):
    sql = """CREATE TABLE IF NOT EXISTS tag_map (
                item_id integer NOT NULL,
                tag_id integer NOT NULL,
                PRIMARY KEY (item_id, tag_id),
                FOREIGN KEY (item_id) REFERENCES items (item_id),
                FOREIGN KEY (tag_id) REFERENCES tags (tag_id)
                );"""
    con = sqlite3.connect(db)
    con.execute(sql)
    con.close()

# Create Schedule table
def create_schedule_table(db):
    sql = """CREATE TABLE IF NOT EXISTS schedule (
                active_id integer PRIMARY KEY,
                item_id integer NOT NULL,
                start datetime NOT NULL,
                duration integer NOT NULL,
                description text,
                completed boolean,
                FOREIGN KEY (item_id) REFERENCES items (item_id)
                );"""
    con = sqlite3.connect(db)
    con.execute(sql)
    con.close()


# Create Rating table
def create_rating_table(db):
    sql = """CREATE TABLE IF NOT EXISTS ratings (
                date date PRIMARY KEY,
                rating integer
                );"""
    con = sqlite3.connect(db)
    con.execute(sql)
    con.close()

# User defined function
def time_overlap(item_type_a, start_a, duration_a, item_type_b, start_b, duration_b):
    """
        User Defined Function that prevents you from scheduling
        two items of the same type with overlapping times.
        I am doing this because I'm not sure how I would display
        two Tasks or timeframes that have overlapping times

        Created in the database with sqlite3.create_function
        in the create_schedule_table function

        I am not currently using this. Instead I made a time_overlap function
        in the db_interface that is run every time you call the create_schedule_item function. It accomplishes the same thing but I think it is less efficient.
        I don't really know SQLite enough to create a CHECK constraint on the table from Python
    """
    if item_type_a != item_type_b:
        return False
    starts_before_ends = datetime.fromisoformat(start_a) <= (datetime.fromisoformat(start_b) + timedelta(minutes=duration_b))
    ends_after_starts = (datetime.fromisoformat(start_a) + timedelta(minutes=duration_a)) >= datetime.fromisoformat(start_b)

    return (starts_before_ends and ends_after_starts)

def main(db):
    print("I'm main in init db", db)
    init_db(db)
    create_items_table(db)
    create_tags_table(db)
    create_tag_map_table(db)
    create_schedule_table(db)
    create_rating_table(db)
    #create_time_overlap_udf(db)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 't':
            filename = "testing.db"
        elif sys.argv[1] == 'u':
            filename = "unit-test.db"
        else:
            filename = f"{sys.argv[1]}"
    else:
        filename = "daybuilder.db"

    db = os.path.join("..", "tests", filename)
    main(db)

