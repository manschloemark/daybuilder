from calendar import monthrange
from collections import defaultdict
from utils import db_interface, stats, util
import datetime
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QBrush, QPalette, QPainter, QColor
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QDateEdit, QGridLayout, QPushButton, QVBoxLayout, QApplication, QStyleOption, QStyle, QComboBox, QCalendarWidget, QRadioButton, QStackedLayout, QCheckBox, QTextEdit
import sqlite3
import sys


class BarGraph(QWidget):
    def __init__(self, *args, **kwargs):
        super(BarGraph, self).__init__(*args, **kwargs)
        self.grid = QGridLayout(self)
        self.title = QLabel()
        self.graph_container = QWidget()
        self.graph = QVBoxLayout(self.graph_container)

class StatsView(QWidget):
    """Widget that reads the daily planner database
    and highlights interesting correlations"""
    def __init__(self, db, *args, **kwargs):
        super(StatsView, self).__init__(*args, **kwargs)
        self.db = db
        self.grid = QGridLayout(self)
        self.ratings, self.items = None, None

        mainlabel = QLabel("My Stats")
        mainlabel.setProperty("font-class", "title")

        # START FROM SCRATCH. MAKE THE DRAFT FROM THE WHITEBOARD
        # DO ALL OF THE SIMPLEST LABEL STUFF FIRST.
        # LAST THING TO DO IS THE DIY-BAR GRAPH. MAKE A CUSTOM WIDGET FOR THAT.
        # Overall General Stats
        o_avg_rating = QLabel("Average Rating")
        o_avg_rating.setProperty("font-class", "heading")
        o_task_completion = QLabel("Tasks Completed")
        o_task_completion.setProperty("font-class", "heading")
        self.overall_rating = QLabel()
        self.overall_rating.setProperty("font-class", "content")
        self.overall_completion = QLabel()
        self.overall_completion.setProperty("font-class", "content")

        self.grid.addWidget(mainlabel, 0, 0, 1, 5)
        #self.grid.addWidget(overall_label, 1, 0, alignment=Qt.AlignLeft)
        self.grid.addWidget(o_avg_rating, 2, 0, 1, 2, alignment=Qt.AlignCenter)
        self.grid.addWidget(o_task_completion, 2, 3, 1, 2, alignment=Qt.AlignCenter)
        self.grid.addWidget(self.overall_rating, 3, 0, 1, 2, alignment=Qt.AlignCenter)
        self.grid.addWidget(self.overall_completion, 3, 3, 1, 2, alignment=Qt.AlignCenter)

        # Detailed Task Stats
        task_label = QLabel("tasks")
        task_label.setProperty("font-class", "sub-heading")
        most_common_task = QLabel("Most Common Task:")
        most_common_task.setProperty("font-class", "detail")
        most_completed_task = QLabel("Highest Completion Rate:")
        most_completed_task.setProperty("font-class", "detail")
        least_completed_task = QLabel("Lowest Completion Rate:")
        least_completed_task.setProperty("font-class", "detail")

        self.most_common = QLabel()
        self.most_common.setProperty("font-class", "subcontent")
        self.most_completed = QLabel()
        self.most_completed.setProperty("font-class", "subcontent")
        self.least_completed = QLabel()
        self.least_completed.setProperty("font-class", "subcontent")

        #self.grid.addWidget(task_label, 4, 0, alignment=Qt.AlignLeft)
        self.grid.addWidget(most_common_task, 5, 0, 1, 2)
        self.grid.addWidget(self.most_common, 5, 2, 1, 2)
        self.grid.addWidget(most_completed_task, 6, 0, 1, 2)
        self.grid.addWidget(self.most_completed, 6, 2, 1, 2)
        self.grid.addWidget(least_completed_task, 7, 0, 1, 2)
        self.grid.addWidget(self.least_completed, 7, 2, 1, 2)

        self.grid.setAlignment(Qt.AlignCenter)
        self.refresh()

    def display_stats(self):
        if self.ratings and self.items:
            self.display_overall_stats()
            self.display_task_stats()

    def get_data(self):
        self.ratings, self.items = stats.load_data(self.db)

    def display_overall_stats(self):
        avg_rating = self.ratings.rating.mean()
        # TODO : can make this more descriptive by
        # treating a number like 2.5 as being a mix of "Bad" and "Okay"
        # instead of just rounding
        avg_rating_word = util.rating_value_map[round(avg_rating)]
        self.overall_rating.setText(f"{avg_rating:.2} ({avg_rating_word})")
        rating_counts = self.ratings.rating.value_counts()
        task_completion = self.items["completed"].value_counts(normalize=True)[True] * 100
        self.overall_completion.setText(
                f"{round(task_completion, 2)}%"
                )

    def display_task_stats(self):
        # NOTE there has to be a better way to do this
        tasks = self.items[self.items.item_type==0]
        task_counts = tasks.item_name.value_counts()
        self.most_common.setText(task_counts.index[0])

        # This returns a sorted pandas.Series containing each item_name and the % they are completed
        # and not completed
        # TODO : figure out how to extract the item name with the highest True % and one with the highest False % (lowest True)
        comp_rates = tasks.groupby("item_name").completed.value_counts(normalize=True)
        comp_rates_true = comp_rates[comp_rates.index.get_level_values('completed').isin([True])].sort_values()

        worst_name, worst_rate = comp_rates_true.head(1).index[0][0], comp_rates_true.head(1)[0]
        best_name, best_rate = comp_rates_true.tail(1).index[0][0], comp_rates_true.tail(1)[0]

        self.most_completed.setText(f"{best_name} ({round(best_rate * 100)}%)")
        self.least_completed.setText(f"{worst_name} ({round(worst_rate * 100)}%)")

    def display_weekday_stats(self):
        weekday_ratings = self.ratings.groupby(by=self.ratings.date.dt.weekday)
        for name, group in weekday_ratings:
            day_index = (name + 1) % 7
            print(f" Name = {name}, Day = {util.weekday_map[day_index]}")
            print(group.rating.value_counts())
            print(group.rating.agg(["count", "mean"]))

    def refresh(self):
        self.get_data()
        self.display_stats()

def main():
    if len(sys.argv) > 1:
        db = f"tests/{sys.argv[1]}"
    else:
        db = "tests/randy.db"
    app = QApplication([])
    stat = StatsView(db)
    with open("stats_styles.qss") as styles:
        stat.setStyleSheet(styles.read())
    stat.show()
    app.exec_()



if __name__ == "__main__":
    main()


