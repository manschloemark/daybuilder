from collections import defaultdict
from daybuilder.widgets.rating import DailyRating
from daybuilder.widgets import scheduleitem
from daybuilder.utils import db_interface, util
from datetime import date, datetime, time, timedelta
import logging
import os
import sqlite3
from PyQt5.QtCore import Qt, pyqtSignal, QDate, QTime
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QDockWidget,
    QWidget,
    QLabel,
    QTextEdit,
    QCalendarWidget,
    QGridLayout,
    QScrollArea,
    QStackedLayout,
    QLineEdit,
    QDateEdit,
    QTimeEdit,
    QGroupBox,
    QButtonGroup,
    QRadioButton,
    QCheckBox,
    QMessageBox,
    QSizePolicy,
)
import sys

logging.basicConfig()

# Globals
DATE_LABEL_FORMAT = "%A, %B %d %Y"
QDATE_LABEL_FORMAT = "ddd, MMM d yyyy"
# --------
# This is a useful function but I'm not sure where it belongs yet
def load_schedule(self):
    with sqlite3.connect(self.db) as con:
        con.row_factory = sqlite3.Row
        rows = db_interface.get_schedule(con)
        for row in rows:
            day = datetime.fromisoformat(row["start"]).date()
            item = scheduleitem.get_item(row)
            self.schedule[day].append(item)


class DailyPlanner(QWidget):
    def __init__(self, db, *args, **kwargs):
        super(DailyPlanner, self).__init__(*args, **kwargs)
        self.db = db
        self.grid = QGridLayout(self)

        self.setWindowTitle("Day Builder")

        self.schedule_area = ScheduleArea(self.db, parent=self)

        self.date_control = DateControl(parent=self)
        self.date_control.calendar.selectionChanged.connect(self.date_changed)

        self.daily_rating = DailyRating()
        self.daily_rating.choices.idClicked.connect(self.save_rating)

        self.planner = Planner(self.db, parent=self)
        self.planner.item_scheduled.connect(lambda: self.schedule_area.refresh(self.date_control.date))

        self.view_date = self.date_control.date
        self.date_changed()

        self.grid.addWidget(self.date_control, 0, 0)
        self.grid.addWidget(self.daily_rating, 0, 1, 2, 1)
        self.grid.addWidget(self.schedule_area, 1, 0, 2, 1)
        self.grid.addWidget(self.planner, 2, 1)

        self.grid.setColumnStretch(0, 5)
        self.grid.setRowStretch(2, 5)

    def date_changed(self):
        self.view_date = self.date_control.date
        self.schedule_area.refresh(self.view_date)
        self.schedule_area.fix_scroll_area()
        new_rating = self.get_rating()
        self.daily_rating.refresh(new_rating, self.view_date)

    def get_rating(self):
        with sqlite3.connect(self.db) as con:
            rating = db_interface.get_rating_by_date(con, self.view_date)
        return rating

    def save_rating(self, rating):
        if rating == -1:
            return
        with sqlite3.connect(self.db) as con:
            if db_interface.get_rating_by_date(con, self.view_date):
                db_interface.update_rating_row(con, self.view_date, rating)
            else:
                db_interface.insert_rating_row(con, self.view_date, rating)


class ScheduleArea(QWidget):
    def __init__(self, db, *args, **kwargs):
        super(ScheduleArea, self).__init__(*args, **kwargs)
        self.vbox = QVBoxLayout(self)
        self.db = db
        self.items = []
        self.contents = QWidget()
        self.contents.setProperty("id", "schedule-area")
        self.content_grid = QVBoxLayout(self.contents)
        self.empty_message = QLabel("There are currently no plans.")
        self.empty_message.setProperty("font-class", "content")
        self.content_grid.addWidget(self.empty_message)#, 0, 1, 1, 1)
        self.content_grid.setAlignment(self.empty_message, Qt.AlignCenter)
        self.empty_message.hide()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_area.setWidget(self.contents)

        self.vbox.addWidget(self.scroll_area)

    def load_schedule(self):
        self.items = []
        with sqlite3.connect(self.db) as con:
            con.row_factory = sqlite3.Row
            rows = db_interface.get_schedule_by_date(con, self.view_date)
            for row in rows:
                # This line is honestly redundant but I'll leave it just in case
                day = datetime.fromisoformat(row["start"]).date()
                item = scheduleitem.get_item(row)
                item.updated.connect(self.update_item)
                item.deleted.connect(self.delete_item)
                self.items.append(item)

    def display_items(self):
        """ This will need huge reworks to make it so it is placing
        the widgets in a more regular and aesthetic fashion
        So this function is terrible because it's 12am and I just realized I messed it up by switching to a vbox from a grid and I am just trying to make it work since the project is due tomorrow morning
        """
        NUM_COLS = 3
        NUM_ROWS = 24 * 4  # The grid will have 4 rows for every hour
        if len(self.items) == 0:
            self.display_no_items()
        else:
            if self.empty_message.isVisible():
                self.empty_message.hide()
            # get timeframes
            qeue = []
            for item in sorted(self.items, key=lambda i: i.start):
                if item.item_type == 1:
                    qeue.append(item)
                elif item.item_type == 0:
                    plotted = False
                    for other_item in self.items:
                        if other_item.item_type == 1 and item.overlaps(other_item):
                            plotted = True
                            other_item.add_task(item)
                            break
                    if not plotted:
                        qeue.append(item)
            for widget in qeue:
                self.content_grid.addWidget(widget)

    def fix_scroll_area(self):
        """ Set the scroll area to scroll to the top
            This is meant to be called when you change page """
        # TODO make it so when a scheduleitem is updated this scrolls
        # back to that item instead of the top.
        # And make sure the scroll area is wide enough to show the entire schedule item
        #self.scroll_area.setMinimumWidth(self.content_grid.itemAt(0).widget().sizeHint().width() + 20)
        self.scroll_area.ensureVisible(0, 0)

    def display_no_items(self):
        self.empty_message.show()
        self.scroll_area.ensureWidgetVisible(self.empty_message)

    # NOTE to self:
    #      I use deleteLater here to clear the view because
    #      my previous solution, setParent(None) was causing
    #      log messages to appear.
    #      The message was something like:
    #      xcb error: BadWindow
    #
    #      Except with a lot more text so it filled up the terminal.
    #
    #      For some reasons those messages only appeared when using
    #      kvantum themes.
    #
    #      I suppose it makes sense, because None is certainly not a valid window.
    #
    #      Using deleteLater here means the program is more wasteful when
    #      updating an item.
    #      the update_item method calls refresh which calls clear_view.
    #      Previously it wasn't as bad because the widgets were not deleted, they
    #      just didn't have a parent. You could immediately call display_items after
    #      clear_view because you still had the widgets in a list.
    #      Now the widgets get deleted so the refresh method has to call load_schedule
    #      after clear_view every time.
    #
    #      So now doing something as simple as marking a task as complete deletes the
    #      entire schedule and you have to access the database to rebuild the items
    #
    #      Additionally, tasks calling the update_item method when they are marked as complete
    #      is wasteful on it's own. The only reason I do that is because it was faster at the time.
    #      The update_item method calls refresh because it is used when any scheudle item is updated,
    #      regardless of the reason, and in the event of updating an item time, it may require the
    #      items to be rearranged.
    #
    #      Fortunately this app takes place on a small enough scale that this doesn't matter.
    #
    #      The alternative to this is writing an algorithm that checks each items times to see if
    #      they need to be reordered after an update.
    #      And maybe making a different method that only marks an item as complete.
    #
    #      I'll keep this in mind when I do a rewrite.

    def clear_view(self):
        logging.debug("Before delete: %d", self.content_grid.count())
        for i in reversed(range(self.content_grid.count())):
            if self.content_grid.itemAt(i).widget() is not self.empty_message:
                self.content_grid.itemAt(i).widget().deleteLater()
        logging.debug("After delete: %d", self.content_grid.count())

    def delete_item(self, active_id):
        with sqlite3.connect(self.db) as con:
            db_interface.delete_schedule_item(con, active_id)
        self.refresh()

    def update_item(self, args):
        with sqlite3.connect(self.db) as con:
            db_interface.update_schedule_item(con, *args)
        self.refresh()

    def refresh(self, new_date=None):
        self.clear_view()
        if new_date:
            self.view_date = new_date
        self.load_schedule()
        self.display_items()



class DateControl(QWidget):
    """ Custom widget that will be used to change the date for the schedule viewer. I have decided to make a custom class for this so I can keep all of the code in one place """

    date_changed = pyqtSignal()
    day_rated = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super(DateControl, self).__init__(*args, **kwargs)
        self.vbox = QVBoxLayout(self)
        self.container = QWidget()
        self.vbox.addWidget(self.container)

        self.calendar = QCalendarWidget()
        self.vbox.addWidget(self.calendar)
        self.calendar.hide()
        self.calendar.selectionChanged.connect(self.calendar_date_selected)

        self.hbox = QHBoxLayout(self.container)
        self.date_minus_button = QPushButton(
            icon=util.back_icon())
        self.date_minus_button.clicked.connect(self.back_one_day)
        self.date_label = QPushButton(
            icon=util.new_date_icon(),
            text=self.qdate.toString(QDATE_LABEL_FORMAT),
        )
        self.date_label.clicked.connect(self.open_calendar)
        self.date_plus_button = QPushButton(icon=util.forward_icon())

        self.date_plus_button.clicked.connect(self.forward_one_day)
        self.hbox.addWidget(self.date_minus_button)
        self.hbox.addWidget(self.date_label)
        self.hbox.addWidget(self.date_plus_button)

        self.date_minus_button.setProperty("qclass", "date-control-button")
        self.date_plus_button.setProperty("qclass", "date-control-button")
        self.date_label.setProperty("id", "date-control")

    @property
    def date(self):
        """
            Convert the QDate object from the QCalendarWidget to a
            date object from Python's native datetime library
            It feels kind of wasteful since this literally calls the
            qdate property three times but it is convenient for now.
        """
        return date(self.qdate.year(), self.qdate.month(), self.qdate.day())

    @property
    def qdate(self):
        """
            Using this to make it easier to refer to the calendar's current date
            I don't know if this is bad practice or not.
        """
        return self.calendar.selectedDate()

    def back_one_day(self):
        self.calendar.setSelectedDate(self.qdate.addDays(-1))

    def forward_one_day(self):
        self.calendar.setSelectedDate(self.qdate.addDays(1))

    def open_calendar(self):
        if self.calendar.isHidden():
            self.calendar.show()
        else:
            self.calendar.hide()
        # self.date_label.setEnabled(False)
        # self.date_minus_button.setEnabled(False)
        # self.date_plus_button.setEnabled(False)
        # self.calendar = QCalendarWidget()
        # self.calendar.setSelectedDate(self.date)

    def calendar_date_selected(self):
        # qdate = self.calendar.selectedDate()
        # self.date = date(qdate.year(), qdate.month(), qdate.day())

        # self.date_label.setEnabled(True)
        # self.date_minus_button.setEnabled(True)
        # self.date_plus_button.setEnabled(True)
        self.refresh()

    def refresh(self):
        self.date_label.setText(self.qdate.toString(QDATE_LABEL_FORMAT))

# This is a temporary place for this dictionary.
# It will probably be moved to the ScheduleItem module at some point
# This will be used to create radio buttons for the item creation form.

class Planner(QWidget):
    """
        Widget that will be in the dock of the main window.
        Lets users make new plans
    """
    item_scheduled = pyqtSignal()
    def __init__(self, db, *args, **kwargs):
        super(Planner, self).__init__(*args, **kwargs)
        self.db = db

        self.stack = QStackedLayout(self)
        self.form = ScheduleForm(db)
        self.form.item_planned.connect(self.update_plans)

        self.selection = QWidget()
        self.vbox = QVBoxLayout(self.selection)

        self.stack.addWidget(self.selection)
        self.stack.addWidget(self.form)

        self.form.cancel_button.clicked.connect(self.lower_form)

        template_label = QLabel("Quick Reuse")
        template_label.setProperty("font-class", "sub-heading")

        self.template_container = QWidget()
        self.template_vbox = QVBoxLayout(self.template_container)
        self.template_vbox.setAlignment(Qt.AlignTop)
        self.template_scroll_area = QScrollArea()
        self.template_scroll_area.setWidgetResizable(True)
        self.template_scroll_area.setWidget(self.template_container)

        self.template_map = {}
        for type_id, type_name in util.item_types.items():
            type_container = QGroupBox(title=type_name+'s')
            type_container.setFlat(True)
            type_container.setProperty("qclass", "item-type-title")
            layout = QVBoxLayout(type_container)
            self.template_vbox.addWidget(type_container)
            self.template_map[type_id] = layout


        # TODO: implement controls that let you sort and filter the
        # list of templates.
        # Sort by date used, alphabetically, tags, let the user search by name
        self.template_control_container = QWidget()
        self.template_control_vbox = QHBoxLayout(self.template_control_container)
        self.template_control_vbox.setAlignment(Qt.AlignCenter)
        sort_label = QLabel("Sort:")
        self.sortby_alpha = QRadioButton("alphabetically")
        self.sortby_alpha.setChecked(True)
        self.sortby_alpha.clicked.connect(self.display_templates)
        self.sortby_count = QRadioButton("by count")
        self.sortby_count.clicked.connect(self.display_templates)
        self.sort_reversed = QCheckBox("reverse")
        self.sort_reversed.clicked.connect(self.display_templates)

        self.template_control_vbox.addWidget(sort_label)
        self.template_control_vbox.addWidget(self.sortby_alpha)
        self.template_control_vbox.addWidget(self.sortby_count)
        self.template_control_vbox.addWidget(self.sort_reversed)

        sort_label.setProperty("font-class", "detail")
        self.sortby_alpha.setProperty("font-class", "detail")
        self.sortby_count.setProperty("font-class", "detail")
        self.sort_reversed.setProperty("font-class", "detail")

        self.new_item = QPushButton("New Plan")
        self.new_item.setProperty("id", "new-item")
        self.new_item.clicked.connect(self.raise_form)

        self.vbox.addWidget(self.new_item)
        self.vbox.addWidget(template_label)
        self.vbox.addWidget(self.template_scroll_area)
        self.vbox.addWidget(self.template_control_container)
        self.init_templates()

    def lower_form(self):
        self.stack.setCurrentWidget(self.selection)

    def raise_form(self):
        # NOTE: I do not like using double parent widget here
        self.form.reset(self.parentWidget().view_date)
        self.stack.setCurrentWidget(self.form)

    def update_plans(self, item_is_new, active_id):
        with sqlite3.connect(self.db) as con:
            con.row_factory = sqlite3.Row
            new_row = db_interface.get_schedule_item(con, active_id)
            if item_is_new:
                self.append_template(new_row)
        self.lower_form()
        self.item_scheduled.emit()

    def load_templates(self):
        self.templates = []
        with sqlite3.connect(self.db) as con:
            con.row_factory = sqlite3.Row
            rows = db_interface.get_templates(con)
            for row in rows:
                template = TemplateButton(row)
                template.clicked.connect(self.item_from_template)
                self.templates.append(template)

    def display_templates(self):
        if self.sortby_alpha.isChecked():
            self.templates = sorted(self.templates, key=lambda t: t.text(), reverse=self.sort_reversed.isChecked())
        elif self.sortby_count.isChecked():
            self.templates = sorted(self.templates, key=lambda t: t.count, reverse=not self.sort_reversed.isChecked())
        for template in self.templates:
            self.template_map[template.item_type].addWidget(template)

    def append_template(self, row):
        template = TemplateButton(row)
        template.clicked.connect(self.item_from_template)
        self.templates.append(template)
        self.display_templates()

    def init_templates(self):
        self.load_templates()
        self.display_templates()

    def item_from_template(self, data):
        """ Open a new schedule form with some data filled out already """
        # NOTE: I do not like using double parent widget here
        self.raise_form()
        self.form.get_template_data(*data)


class TemplateButton(QPushButton):
    clicked = pyqtSignal(tuple)

    def __init__(self, row, *args, **kwargs):
        super(TemplateButton, self).__init__(*args, **kwargs)
        self.setProperty("qclass", "template-button")
        self.setText(row['item_name'])
        self.item_type = int(row['item_type'])
        try:
            self.count = int(row['count'])
        except IndexError:
            self.count = 1
        self.setToolTip(str(self.count))
        # TODO: the db_interface needs to be fixed to get the last_used
        # date
        #self.last_used= datetime.fromisoformat(row['start'])

    def mousePressEvent(self, click_event):
        self.clicked.emit((self.item_type, self.text()))

class ScheduleForm(QWidget):
    """ Form that gets Schedule Item info from user """
    item_planned = pyqtSignal(bool, int)
    def __init__(self, db, *args, **kwargs):
        super(ScheduleForm, self).__init__(*args, **kwargs)
        self.db = db
        self.grid = QGridLayout(self)

        self.item_type_container = QGroupBox("*Item Type:")
        self.item_type_buttons = QButtonGroup()
        self.item_type_vbox = QVBoxLayout()
        for id_number, item_type in util.item_types.items():
            radio_button = QRadioButton(text=item_type)
            self.item_type_vbox.addWidget(radio_button)
            self.item_type_buttons.addButton(radio_button)
            self.item_type_buttons.setId(radio_button, id_number)
        self.item_type_container.setLayout(self.item_type_vbox)

        name_label = QLabel("*Name:")
        self.name_entry = QLineEdit()
        description_label = QLabel("Description:")
        self.description_entry = QTextEdit()
        tags_label = QLabel("Tags:")
        self.tags = None #TODO : decide what to do with tags
        date_label= QLabel("*Date:")
        self.day = QDateEdit()
        start_label=QLabel("*Start Time:")
        self.start = QTimeEdit()
        self.end_time_checkbox = QCheckBox("End Time:")
        self.end_time_checkbox.setChecked(True)
        self.end_time_checkbox.clicked.connect(self.end_time_checked)
        self.end = QTimeEdit()

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.validate)
        self.cancel_button = QPushButton("Cancel")

        self.grid.addWidget(self.item_type_container, 0, 0, 2, 3)
        self.grid.addWidget(name_label, 2, 0)
        self.grid.addWidget(self.name_entry, 2, 1, 1, 2)
        self.grid.addWidget(description_label, 3, 0)
        self.grid.addWidget(self.description_entry, 3, 1, 2, 2)
        self.grid.addWidget(date_label, 5, 0)
        self.grid.addWidget(self.day, 5, 1, 1, 2)
        self.grid.addWidget(start_label, 6, 0)
        self.grid.addWidget(self.start, 6, 1, 1, 2)
        self.grid.addWidget(self.end_time_checkbox, 7, 0)
        self.grid.addWidget(self.end, 7, 1, 1, 2)
        self.grid.addWidget(self.submit_button, 8, 0, 1, 2)
        self.grid.addWidget(self.cancel_button, 8, 2)

        self.grid.setAlignment(description_label, Qt.AlignTop)

    def end_time_checked(self):
        if self.end_time_checkbox.isChecked():
            self.end.setDisabled(False)
        else:
            self.end.setDisabled(True)

    def reset(self, active_date):
        if self.item_type_buttons.checkedButton():
            self.item_type_buttons.checkedButton().setChecked(False)
        self.name_entry.clear()
        self.description_entry.clear()
        # I want to set this to the date currently selected by the DateControl.
        self.day.setDate(active_date)
        # Set time to next hour
        self.start.setTime(QTime(QTime.currentTime().hour(), 0).addSecs(60*60))
        # Set end time to 2nd nearest hour
        self.end.setTime(self.start.time().addSecs(60*60))

    def get_template_data(self, item_type, item_name):
        self.item_type_buttons.button(item_type).setChecked(True)
        self.name_entry.setText(item_name)

    def validate(self):
        # Go through each field and make sure they make sense
        warnings = []
        item_type = self.item_type_buttons.checkedId()
        item_name = self.name_entry.text()
        # TODO: tag stuff
        tags = None
        description = self.description_entry.toPlainText()
        qday = self.day.date()
        start_qtime = self.start.time()
        start_datetime = datetime(qday.year(), qday.month(), qday.day(), start_qtime.hour(), start_qtime.minute())
        if self.end_time_checkbox.isChecked():
            end_qtime = self.end.time()
            if start_qtime > end_qtime:
                warnings.append("Start time should be earlier than End time")
            duration = (datetime(qday.year(), qday.month(), qday.day(), end_qtime.hour(), end_qtime.minute()) - start_datetime).seconds / 60
        else:
            duration = 0
        if item_type == -1:
            warnings.append("You must select an item type.")
        if item_name == "":
            warnings.append("You must enter a name")
        if len(warnings) >= 1:
            msg = QMessageBox()
            msg.warning(self, f"Invalid Info! [{len(warnings)}]", "\n\n".join(warnings), QMessageBox.Ok)
            return

        self.submit_data(item_type, item_name, tags, description, start_datetime, duration)

    def submit_data(self, item_type, item_name, tags, description, start, duration):
        with sqlite3.connect(self.db) as con:
            new_item = not db_interface.item_exists(con, item_type, item_name)
            try:
                active_id = db_interface.create_schedule_item(
                                                          con,
                                                          item_type,
                                                          item_name,
                                                          tags,
                                                          description,
                                                          start,
                                                          duration
                                                         )
            except db_interface.TimeOverlapError:
                msg = QMessageBox()
                msg.warning(self, "Invalid Time", "That items time conflicted with another planned item of the same type")
                return

        self.item_planned.emit(new_item, active_id)

def main():
    if len(sys.argv) > 1:
        #logging.getLogger(__name__).setLevel(logging.DEBUG)
        db = "tests/" + sys.argv[1]
    else:
        db = "tests/testing.db"
    app = QApplication([])
    daybuilder = DailyPlanner(db)
    daybuilder.show()
    app.exec_()

if __name__ == "__main__":
    main()

