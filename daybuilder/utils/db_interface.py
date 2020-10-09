"""
    Module used to handle all interactions with the database
    The purpose of this is to ensure there is a consistent
    format for data flow in this application.
"""
# db_interface.py
import logging
import sqlite3
from PyQt5.QtCore import QDateTime, QDate, Qt

logger = logging.getLogger(__name__)

class TimeOverlapError(Exception):
    pass

# --- Items Table
def insert_item(con, item_type, item_name):
    sql = "INSERT INTO items (item_type, item_name) VALUES (?, ?)"
    cur = con.cursor()
    cur.execute(sql, (item_type, item_name))
    new_id = cur.lastrowid
    return new_id


def get_item_type(con, item_id):
    sql = "SELECT item_type FROM items WHERE item_id = ?"
    cur = con.cursor()
    cur.execute(sql, (item_id,))
    item_type = cur.fetchone()
    if item_type:
        item_type = item_type[0]
    return item_type


def get_item_id(con, item_type, item_name):
    sql = "SELECT item_id FROM items WHERE item_type = ? AND item_name = ?"
    cur = con.cursor()
    cur.execute(sql, (item_type, item_name))
    item_id = cur.fetchone()
    if item_id is None:
        item_id = insert_item(con, item_type, item_name)
    else:
        item_id = item_id[0]
    return item_id


# --- Tags Table

def insert_tag(con, tag_name):
    sql = "INSERT INTO tags (tag_name) VALUES (?)"
    cur = con.cursor()
    cur.execute(sql, (tag_name,))
    tag_id = cur.lastrowid
    return tag_id

def get_tag_id(con, tag_name):
    sql = "SELECT tag_id FROM tags where tag_name = ?"
    cur = con.cursor()
    cur.execute(sql, (tag_name,))
    tag_id = cur.fetchone()
    if tag_id is None:
        tag_id = insert_tag(con, tag_name)
    else:
        tag_id = tag_id[0] # since cursor.fetchone returns a tuple
    return tag_id


# --- Tag_Map Table

def insert_tag_map(con, item_id, tag_id):
    # This function should check to make sure there is not a row that already
    # contains these values
    sql = "INSERT INTO tag_map (item_id, tag_id) VALUES (?, ?)"
    cur = con.cursor()
    cur.execute(sql, (item_id, tag_id))


def get_item_tags(con, item_id):
    sql = """SELECT tag_name FROM tag_map
            INNER JOIN tags ON tags.tag_id = tag_map.tag_id
            WHERE tag_map.item_id = ?"""
    cur = con.cursor()
    cur.execute(sql, (item_id,))

    rows = cur.fetchall()
    # tags is a list of tuples that contain one tag_name
    # I would rather have a list of tag_names.
    # This is tough because the way you handle this is totally dependant on the row_factory...
    tags = [row['tag_name'] for row in rows]

    return tags

def get_items_with_tag(con, tag_id):
    sql = """SELECT item_id FROM tag_map
            INNER JOIN items ON tag_map.item_id = items.item_id
            WHERE tag_map.tag_id = ?"""
    cur = con.cursor()
    cur.execute(sql, (tag_id,))

    items = cur.fetchall()
    return items


# --- Schedule Table

def insert_schedule_row(con, item_id, description, start, duration, completed):
    sql = """INSERT INTO schedule (item_id, description, start, duration, completed) VALUES (?, ?, ?, ?, ?)"""

    cur = con.cursor()
    cur.execute(sql, (item_id, description, start, duration, completed))

    active_item_id = cur.lastrowid
    return active_item_id

def get_schedule_table(con):
    sql = "SELECT * FROM schedule"

    cur = con.cursor()
    cur.execute(sql)

    schedule = cur.fetchall()
    return schedule

# --- Daily Rating Table

def insert_rating_row(con, date, rating):
    sql = "INSERT INTO ratings VALUES (?, ?)"
    isodate = date.toString(Qt.ISODate)
    cur = con.cursor()
    cur.execute(sql, (isodate, rating))

def update_rating_row(con, date, rating):
    sql = "UPDATE ratings SET rating = ? WHERE date = ?"
    isodate = date.toString(Qt.ISODate)
    cur = con.cursor()
    cur.execute(sql, (rating, isodate))

def get_ratings(con, oldest_date, newest_date):
    sql = "SELECT * FROM ratings"
    
    args = []
    if oldest_date or newest_date:
        sql += " WHERE"
    if oldest_date:
        args.append(oldest_date.toString(Qt.ISODate))
        sql += " date(date) >= ?"
    if newest_date:
        if oldest_date:
            sql += " AND "
        sql += " date(date) <= ?"
        args.append(newest_date.toString(Qt.ISODate))
        
    cur = con.cursor()
    cur.execute(sql, tuple(args))
    rows = cur.fetchall()
    return rows

def get_rating_by_date(con, date):
    sql = "SELECT rating FROM ratings WHERE date = ?"
    isodate = date.toString(Qt.ISODate)
    cur = con.cursor()
    cur.execute(sql, (isodate,))

    rating = cur.fetchone()
    if rating:
        return rating[0]
    return rating


# Higher Level Functions

def get_table_columns(con, tablename):
    """
    Get the column names from a table. I am making this so the stats script is able to create a dataframe even if there are no items in a table.
    It seems like table names are not able to be substituded
    using sqlite3's normal method. I'm going to use python's string
    formatter, but I will have to make sure the string given is not a threat

    Then again, this function would never be called by a user anyway. So I guess it's not really a big deal."""
    # I think that as long as there are only letters this should be safe.
    # I'm not very proud of this though.
    # TODO: check if there is a better way to do this.
    for char in tablename:
        if not char.isalpha() or char == '_':
            raise ValueError
    cur = con.cursor()
    cur.execute(f"SELECT * FROM {tablename}")
    return [item[0] for item in cur.description]

# NOTE I don't know if I need this?
# NOTE If it turns out I do need this I'll have to convert it to
#      work with QDate
# def time_overlap(con, item_type, start, duration):
#     """
#         User Defined Function that prevents you from scheduling
#         two items of the same type with overlapping times.
#         I am doing this because I'm not sure how I would display
#         two Tasks or timeframes that have overlapping times

#         Created in the database with sqlite3.create_function
#         in the create_schedule_table function
#     """
#     con.row_factory = sqlite3.Row # NOTE : there has to be a better way to handle passing database connections around
#     sql = """SELECT item_type, start, duration FROM schedule
#              JOIN items on items.item_id = schedule.item_id"""
#     cur = con.cursor()
#     cur.execute(sql)
#     rows = cur.fetchall()

#     for row in rows:
#         starts_before_ends = QDateTime.fromString(row['start'], Qt.ISODate).addSecs(row[duration * 60])
#         ends_after_starts = 
#         if (item_type == row['item_type']) and starts_before_ends and ends_after_starts:
#             return True
#     return False

# Saving data

def set_tags(con, item_id, tags):
    #TODO I think some higher level code should make sure all strings passed into this are lowercase
    assert isinstance(tags, list)
    for tag in tags:
        if not tag in get_item_tags(con, item_id):
            tag_id = get_tag_id(con, tag)
            insert_tag_map(con, item_id, tag_id)


def create_schedule_item(con, item_type, item_name, tags, description, start, duration):
    if time_overlap(con, item_type, start, duration):
        raise TimeOverlapError()
    item_id = get_item_id(con, item_type, item_name)
    if tags:
        set_tags(con, item_id, tags)
    iso_start = start.isoformat(timespec="minutes")
    if duration is None:
        duration = 0
    # I don't think you will ever schedule an already completed task
    # But maybe the interface should not determine that, maybe it should
    # be left as an option for whoever wants to do that.
    if item_type == 1:
        completed = None
    else:
        completed = 0

    active_id = insert_schedule_row(con, item_id, description, iso_start, duration, completed)

    return active_id

def update_schedule_item(con, active_id, item_id, tags, description, start, duration, completed):
    sql = """
             UPDATE schedule SET description = ?, start = ?, duration = ?, completed = ?
             WHERE active_id = ?;
          """
    if tags:
        set_tags(con, item_id, tags)
    iso_start = start.toString(Qt.ISODate)
    cur = con.cursor()
    cur.execute(sql, (description, iso_start, duration, completed, active_id))

def delete_schedule_item(con, active_id):
    sql = "DELETE FROM schedule WHERE active_id = ?"
    cur = con.cursor()
    cur.execute(sql, (active_id,))

def mark_task_complete(con, active_id, complete):
    sql = "UPDATE schedule SET completed = ? WHERE active_id = ?"
    cur = con.cursor()
    cur.execute(sql, (complete, active_id))


# Reading Data
def item_exists(con, item_type, item_name):
    sql = "SELECT * FROM items WHERE item_type = ? AND item_name = ?"
    cur = con.cursor()
    cur.execute(sql, (item_type, item_name))
    item = cur.fetchone()

    if item:
        return True
    return False

def get_schedule_item_tags(con, active_id):
    sql = "SELECT item_id FROM schedule WHERE active_id = ?;"
    cur = con.cursor()
    cur.execute(sql, (active_id,))
    item_id = cur.fetchone()
    if item_id:
        item_id = item_id[0]

    tags = get_item_tags(con, item_id)

def get_templates(con):
    """
        Select the item type and name from each row in the items table
        This function is intended to be used in the GUI program to build a widget
        containing a button for each unique item.
        This is incomplete because I wanted the templates to have some extra data
        that would allow for them to be sorted.
            ex: I want to select each item_type and item_id joined with the
            most recent start attribute from the schedule table. I just don't
            remember how to do that SQL.
    """
    # TODO: learn SQL again and figure out how to get one row for each unique
    # item_type and item_name joined with the newest start datetime
    sql = """SELECT item_type, item_name, COUNT(*) AS 'count' FROM schedule JOIN items ON schedule.item_id = items.item_id GROUP BY items.item_id"""
    cur = con.cursor()
    cur.execute(sql)
    templates = cur.fetchall()
    return templates

def get_schedule_item(con, active_id):
    sql = """ SELECT active_id, items.item_type, items.item_id, items.item_name, description, start, duration, completed
            FROM schedule
            JOIN items ON items.item_id = schedule.item_id
            WHERE active_id = ?"""
    cur = con.cursor()
    cur.execute(sql, (active_id,))
    row = cur.fetchone()
    return row

def get_schedule_by_date(con, date):
    """ Get rows from the schedule joined with the items table from a single day """
    sql = """ SELECT active_id, items.item_type, items.item_id, items.item_name, description, start, duration, completed
              FROM schedule
              JOIN items ON items.item_id = schedule.item_id
              WHERE date(start) = ?
              ORDER BY start;"""
    iso_date = date.toString(Qt.ISODate)
    cur = con.cursor()
    cur.execute(sql, (iso_date,))
    rows = cur.fetchall()
    return rows


def get_schedule(con, oldest_date=None, newest_date=None):
    """
        Get rows from the schedule table joined with the items table.
        Data from these two tables provides all the information you would
        need to plot them.

        parameters
        oldest_date : datetime.date object. Only select rows from the table
        who have dates that come on or after this date.
        newest_date : datetime.date object. Only select rows from the table
        who have dates that come on or before this date.

        Leave both empty (or None) to select all rows from the table.

    """
    sql = """ SELECT active_id, items.item_type, items.item_id, items.item_name, description, start, duration, completed  FROM schedule
              INNER JOIN items ON schedule.item_id = items.item_id
          """
    oldest_date_sql = " date(start) >= ?"
    newest_date_sql = " date(start) <= ?"
    args = []
    if oldest_date or newest_date:
        sql += " WHERE"
    if oldest_date:
        sql += oldest_date_sql
        args.append(oldest_date.toString(Qt.ISODate))
    if newest_date:
        if oldest_date:
            sql += " AND "
        sql += newest_date_sql
        args.append(newest_date.toString(Qt.ISODate))
    sql += " ORDER BY start;"
    cur = con.cursor()
    cur.execute(sql, tuple(args))
    schedule = cur.fetchall()
    return schedule


# Functions for the statistics feature
def get_schedule_for_stats(con, oldest_date=None, newest_date=None):
    """
        Query the entire DB for data that will be used for statistics.
        Does not include any ids because the stats page does not need
        to access specific items

        Pretty much a copy of the get_schedule function above but
        gets less data to save time and memory
    """
    sql = """
             SELECT item_name, item_type,
             length(description) as description,
             start, duration, completed
             FROM schedule
                JOIN items ON items.item_id = schedule.item_id
          """
    oldest_date_sql = " 'date' >= ?"
    newest_date_sql = " 'date' <= ?"
    args = []
    if oldest_date or newest_date:
        sql += " WHERE"
    if oldest_date:
        if not isinstance(oldest_date, (datetime.datetime, datetime.date)):
            raise ValueError(f'oldest date must be datetime.date, not {type(oldest_date)}')
        sql += oldest_date_sql
        args.append(oldest_date.toString(Qt.ISODate))
    if newest_date:
        if not isinstance(newest_date, (datetime.datetime, datetime.date)):
            raise ValueError(f'newest date must be datetime.date, not {type(newest_date)}')
        if oldest_date:
            sql += " AND "
        sql += newest_date_sql
        args.append(newest_date.toString(Qt.ISODate))
    sql += " ORDER BY schedule.start;"
    cur = con.cursor()
    cur.execute(sql, tuple(args))
    rows = cur.fetchall()
    return rows

def get_ratings_for_stats(con):
    sql = "SELECT date, rating FROM ratings;"
    cur = con.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    return rows

def get_avg_rating(con):
    sql = "SELECT avg(rating) FROM ratings;"

    cur = con.cursor()
    cur.execute(sql)
    avg_rating = cur.fetchone()
    if avg_rating:
        return avg_rating[0]
    else:
        return avg_rating
