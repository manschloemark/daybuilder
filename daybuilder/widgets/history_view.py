from calendar import monthrange
from collections import defaultdict
from utils import db_interface, util
import datetime
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QBrush, QPalette, QPainter, QColor
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QDateEdit, QGridLayout, QPushButton, QVBoxLayout, QApplication, QStyleOption, QStyle, QComboBox, QCalendarWidget, QRadioButton, QStackedLayout, QCheckBox, QSizePolicy, QSpacerItem, QGroupBox
import sqlite3
import sys


#Globals
DATE_EDIT_FORMAT = "MMM d, yyyy"
BLOCK_DATE_FORMAT = "%m/%d/%y"
UTF8_CHECKMARK = '\u2714'
UTF8_X = '\u2718'

class DayBlock(QWidget):
    def __init__(self, view_type, day, rating, total_tasks, completed_tasks, *args, **kwargs):
        super(DayBlock, self).__init__(*args, **kwargs)
        self.setProperty("qclass", "dayblock")
        self.layout = QVBoxLayout(self)
        if view_type == "Weekly":
            weekday_label = QLabel(f'{day.strftime("%A"):<12}')
            weekday_label.setProperty("font-class", "block-weekday")
            self.layout.addWidget(weekday_label)
        date_label = QLabel(day.strftime(BLOCK_DATE_FORMAT))
        date_label.setProperty("font-class", "sub-heading")
        task_string = f'{UTF8_CHECKMARK} {completed_tasks}\n' + \
                      f'{UTF8_X} {total_tasks - completed_tasks}'
        task_label = QLabel(task_string)
        task_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        task_label.setProperty("font-class", "content")

        # Not including a rating label and instead making a legend
        #rating_label = QLabel(f"Rating: {util.rating_value_map[rating]}")
        #rating_label.setProperty("font-class", "detail")
        self.setStyleSheet(f"background-color: {util.rating_color_map[rating]}")

        self.layout.addWidget(date_label)
        self.layout.addWidget(task_label)
        self.layout.setAlignment(date_label, Qt.AlignTop)
        self.layout.setAlignment(task_label, Qt.AlignCenter)


    def paintEvent(self, pain_event):
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)


class HistoryView(QWidget):
    def __init__(self, db, *args, **kwargs):
        super(HistoryView, self).__init__(*args, **kwargs)
        #self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.db = db
        self.setProperty('id', 'history-view')
        self.layout = QGridLayout(self)
        control_container = QWidget()
        self.control_hbox = QHBoxLayout(control_container)
        view_selection_label = QLabel("View Format: ")
        view_selection_label.setProperty("font-class", "sub-heading")
        self.view_selection = QComboBox()
        self.view_selection.addItem("Weekly")
        self.view_selection.addItem("Monthly")
        self.view_selection.setSizePolicy(QSizePolicy(0, 0))
        self.view_selection.currentTextChanged.connect(self.set_view)
        date_label = QLabel("From: ")
        date_label.setProperty("font-class", "sub-heading")
        self.date_entry = QDateEdit(QDate.currentDate())
        self.date_entry.setDisplayFormat(DATE_EDIT_FORMAT)
        self.date_entry.dateChanged.connect(self.load_blocks)
        self.date_entry.setSizePolicy(QSizePolicy(0, 0))

        self.view_container = QWidget()
        self.view_stack = QStackedLayout(self.view_container)
        self.week_view = QWidget()
        self.week_layout = QHBoxLayout(self.week_view)
        self.month_view = QWidget()
        self.month_view.setProperty("id", "month-view")
        self.month_layout = QGridLayout(self.month_view)
        # Set grid column and row stretch so everything is equal
        for i, day in enumerate(util.weekday_map.values()):
            weekday_label = QLabel(f'{day:^16}')
            weekday_label.setProperty("font-class", "weekday-heading")
            self.month_layout.addWidget(weekday_label, 0, i)

        self.week_layout.setAlignment(Qt.AlignTop)
        self.month_layout.setAlignment(Qt.AlignCenter)

        self.view_stack.addWidget(self.week_view)
        self.view_stack.addWidget(self.month_view)

        self.control_hbox.addWidget(view_selection_label)
        self.control_hbox.addWidget(self.view_selection)
        self.control_hbox.addSpacing(16)
        self.control_hbox.addWidget(date_label)
        self.control_hbox.addWidget(self.date_entry)
        self.control_hbox.setAlignment(Qt.AlignCenter)

        self.view_legend = QGroupBox("Daily Rating Legend")
        self.view_legend.setProperty("font-class", "detail")
        self.view_legend.setSizePolicy(QSizePolicy(0, 0))
        self.legend_layout = QHBoxLayout(self.view_legend)
        for key, rating in util.rating_value_map.items():
            label = QLabel(f"{rating}:")
            label.setProperty("qclass", "legend")
            sample = QWidget()
            sample.setMinimumSize(16, 16)
            sample.setMaximumSize(16, 16)
            sample.setStyleSheet(f"background-color: {util.rating_color_map[key]};")
            self.legend_layout.addWidget(label)
            self.legend_layout.addWidget(sample)
            if key != 5:
                self.legend_layout.addSpacing(12)
        self.legend_layout.setAlignment(Qt.AlignLeft)

        self.layout.addWidget(control_container, 0, 0, 1, 6)
        self.layout.addWidget(self.view_container, 1, 0, 2, 6)
        self.layout.addWidget(self.view_legend, 3, 0, 1, 6)

        self.set_view()
        # By default load from most recent Sunday
        last_sunday = datetime.date.today() - datetime.timedelta(days=(datetime.date.today().weekday() % 6) + 1)
        self.date_entry.setDate(last_sunday)

        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setAlignment(self.view_legend, Qt.AlignCenter)

    def set_view(self):
        if self.view_selection.currentText() == "Weekly":
            self.month_view.hide()
            self.view_stack.setCurrentWidget(self.week_view)
            self.block_layout = self.week_layout
        elif self.view_selection.currentText() == "Monthly":
            self.month_view.show()
            self.view_stack.setCurrentWidget(self.month_view)
            self.block_layout = self.month_layout
        self.load_blocks()

    def clear_container(self):
        """Same algorithm to clear a layout as in ScheduleArea.clear_view"""
        for i in reversed(range(self.block_layout.count())):
            if not isinstance(self.block_layout.itemAt(i).widget(), QLabel):
                self.block_layout.itemAt(i).widget().setParent(None)

    def load_blocks(self):
        self.clear_container()
        qdate = self.date_entry.date()
        view_type = self.view_selection.currentText()
        # defaultdict would work here too, but I need to run
        # a loop to initialize a key for each day in the week
        # anyway
        week = {}
        if view_type == "Weekly":
            start_day = datetime.date(qdate.year(), qdate.month(), qdate.day())
            num_days = 7
        else:
            month_range = monthrange(qdate.year(), qdate.month())
            start_day = datetime.date(qdate.year(), qdate.month(), 1)
            num_days = month_range[1]

        for i in range(num_days):
            end_day = start_day + datetime.timedelta(days=i)
            week[end_day] = []
        with sqlite3.connect(self.db) as con:
            con.row_factory = sqlite3.Row
            rows = db_interface.get_schedule(con, start_day, end_day)
            for row in rows:
                day = datetime.datetime.fromisoformat(row['start']).date()
                week[day].append(row)
            blocks = []
            for day, plans in week.items():
                rating = db_interface.get_rating_by_date(con, day)
                data = enumerate_day(plans)
                block = DayBlock(view_type, day, rating, *data)
                blocks.append(block)
        self.display_blocks(start_day, blocks)

    def display_blocks(self, start_day, blocks):
        if self.view_selection.currentText() == "Weekly":
            for block in blocks:
                self.block_layout.addWidget(block)
        else:
            # I want the monthly view to look like a calendar
            # With Sunday being the leftmost day (column 0) and Saturday the right (column 6)
            # Since python's datetime library refers to Monday as day 0 and Sunday as day 6
            # I have to shift the numbers so Sunday is 0 and Saturday is 6
            start_col = (start_day.weekday() + 1) % 7
            for count, block in enumerate(blocks, start=start_col):
                row = (count // 7) + 1
                column = count % 7
                self.block_layout.addWidget(block, row, column)
                self.block_layout.setAlignment(block, Qt.AlignTop)


def enumerate_day(rows):
    num_tasks = 0
    completed_tasks = 0
    for row in rows:
        if row['item_type'] == 0:
            num_tasks += 1
            if row['completed'] == True:
                completed_tasks += 1
    return num_tasks, completed_tasks


def main():
    if len(sys.argv) > 1:
        db = f"tests/{sys.argv[1]}"
    else:
        db = "tests/randy.db"
    app = QApplication([])
    history = HistoryView(db)
    with open("daybuilder_styles.qss") as styles:
        history.setStyleSheet(styles.read())
    history.show()
    app.exec_()


if __name__ == "__main__":
    main()
