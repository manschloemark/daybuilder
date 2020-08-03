from daybuilder.utils import db_interface as dbx, init_db
import random
import datetime
import os
import sys
import sqlite3
from calendar import monthrange
import time

if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = input("Enter a filename for the fake user: ")
database_file = os.path.join(os.path.dirname(__file__), 'data', filename)
print(database_file)

start_ns = time.time_ns()
# Make database for the random data
init_db.main(database_file)

# Make a bunch of data

# First I gotta make pools that can be randomly pulled from.

# the day number will be random integer between 1 and monthrange(month)[1]

tasks = ("Cook", "Chores", "Exercise", "Read", "Study", "Relax", "Nap", "Walk Dog", "Gaming", "Painting", "Guitar", "Yodel", "School", "Work", "Commute", "Eat")
timeframes = ("Morning", "Night", "Afternoon", "Free Time")

# Start at Jan 1st, 2019 and generate random data each day for two years
day = datetime.date(2019, 1, 1)
for _ in range(365 * 2):
    day = day + datetime.timedelta(days=1)
    # Make a random number of plans for this day, max is 15
    plans = []
    rating = random.randint(0, 5)
    for __ in range(15):
        item_type = not (bool(random.getrandbits(3))) # 1/8 chance to be True
        # Max duration time will be 3 hours
        tags = []
        if item_type:
            item_name = random.choice(timeframes)
            start_time = datetime.time(random.randint(0, 17), random.randint(0, 59))
            duration = random.randint(0, 360)
        else:
            item_name = random.choice(tasks)
            start_time = datetime.time(random.randint(0, 20), random.randint(0, 59))
            duration = random.randint(0, 180)
        description = "".join(random.choice(tasks) for _ in range(0, 8))
        start = datetime.datetime.combine(day, start_time)
        plans.append((item_type, item_name, tags, description, start, duration))
    with sqlite3.connect(database_file) as con:
        for plan in plans:
            try:
                activeid = dbx.create_schedule_item(con, *plan)
                # 50% chance to mark task as completed
                completed = (random.randint(0, 10) > 3 )
                if plan[0] == 0 and completed:
                    dbx.mark_task_complete(con, activeid, True)
            except dbx.TimeOverlapError:
                pass
        # Rate day randomly
        if rating:
            dbx.insert_rating_row(con, day, rating)

elapsed = time.time_ns() - start_ns
print("Done.")
print(f"That took {elapsed} ns ({elapsed / 10**9} seconds)")
