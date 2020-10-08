"""
    Module that receives data from the db_interface and turns it into
    accessible python data structures.

    This is the rewrite.
    Try to keep the code as clean as possible.
    Try to make it easy to maintain.
    Try to make it easy to modify.
"""
from typing import Optional
import sqlite3
from daybuilder.utils import util

from PyQt5.QtWidgets import QWidget, QLabel, QTextEdit, QHBoxLayout, QApplication, QPushButton, QButtonGroup, QTimeEdit, QFrame, QAbstractSpinBox, QSizePolicy, QSpacerItem, QStackedLayout, QLayout, QStackedWidget, QVBoxLayout, QCheckBox, QStyleOption, QStyle
from PyQt5.QtCore import QDate, QDateTime, Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QBrush, QColor, QPalette

# Globals
TIME_FORMAT = "hh:mm A" # ex: 09:00 PM

# TODO I named the QTimeEdits 'start_edit' and 'end_edit'
#      I think I should change these names because they sound like
#      they could easily be method / function names
class ScheduleItem(QWidget):
    """
        Base class for each type of Schedule Item.
        These are made to represent things from the schedule
        table.
        They allow the user to view their plans, update, or delete them.
    """
    item_type = None
    completed = None
    can_have_children = False # Flag determines whether items of this type can have children

    # Signals
    # NOTE Emits all of the data needed for the schedule table
    #      I just declare the signal argument as a tuple because there are about 5 arguments and one of them
    #      could be either a boolean or None.
    #      And it would make the code pretty ugly when in order to specify which signal to use you have to also
    #      type [int, QDateTime, int, str, bool / None]
    #      Technically I could declare the last type as being object, but that doesn't feel good either.
    # NOTE I think an even better solution would be to declare it as
    #      updated = pyqtSignal(int, QDateTime, int, str, None) in this ScheduleItem base class,
    #      and any children who make use of the completed attribute would just reimplement it as
    #      updated = pyqtSignal(int, QDateTime, int, str, bool)
    #      Hmm, I think that might be the way to go.
    updated = pyqtSignal(tuple)
    deleted = pyqtSignal(int) # Emits the active_id

    def __init__(self, row, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_item = None

        self.init_data(row)
        self.init_name()
        self.init_ui()
        self.stop_editing()

    def init_data(self, row:sqlite3.Row):
        self.id = row['active_id']
        self.item_id = row['item_id']
        self.tags = None
        self.name = row['item_name']
        # NOTE should I just make a self.start attribute a QDateTime?
        #      and use self.start.date() or self.start.time() when necessary
        #      I think I am leaning towards that.
        day_time = QDateTime.fromString(row['start'], Qt.ISODate)
        self.day = day_time.date()
        self.start_time = day_time.time()
        self.duration = row['duration']
        self.end_time = self.start_time.addSecs(self.duration * 60)
        self.description = row['description']
        self.completed = bool(row['completed'])
        self.editing = False

    def init_name(self):
        self.name_label = QLabel(self.name)

    def init_ui(self):
        # NOTE the way I set the Schedule Item layout calls for a VBox instead of a vbox.
        # TODO change the vbox to a vbox when you are done with the Schedule Items and do not have
        #      a need for the vbox. I will leave the grid for now in case there is something I am forgetting.
        self.vbox = QVBoxLayout(self)


        # Container for the top row of the widget, contains the name and edit buttons
        topbar = QWidget()
        top_hbox = QHBoxLayout(topbar)

        # Buttons for editing the Schedule Item
        # Ensure that all edit buttons will not exceed their size hints
        edit_button_size_policy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        # Button that causes the widget to enter edit mode
        self.edit_button = QPushButton(icon=util.edit_icon(), text='Edit')
        self.edit_button.setSizePolicy(edit_button_size_policy)
        self.edit_button.clicked.connect(self.start_editing)

        # Container for buttons available in edit mode - save, cancel, delete
        # These buttons cause the widget to exit edit mode
        self.edit_options = QWidget()
        edit_option_hbox = QHBoxLayout(self.edit_options)
        edit_option_hbox.setAlignment(Qt.AlignRight)

        self.save_button = QPushButton(icon=util.save_icon(), text='Save')
        self.save_button.setSizePolicy(edit_button_size_policy)
        self.save_button.clicked.connect(self.save_changes)

        self.cancel_button = QPushButton(icon=util.cancel_icon(), text='Cancel')
        self.cancel_button.setSizePolicy(edit_button_size_policy)
        self.cancel_button.clicked.connect(self.cancel_edit)

        self.delete_button = QPushButton(icon=util.delete_icon(), text='Delete')
        self.delete_button.setSizePolicy(edit_button_size_policy)
        self.delete_button.clicked.connect(lambda x: self.deleted.emit(self.id))

        edit_option_hbox.addWidget(self.save_button)
        edit_option_hbox.addWidget(self.cancel_button)
        edit_option_hbox.addWidget(self.delete_button)
        edit_option_hbox.addWidget(self.edit_button)

        # When the edit button is visible and the save, cancel, and delete buttons are
        # hidden, you need to make sure the widget saves space for three buttons.
        # There will always be at least one button visible, so you only need to have
        # two buttons retain their size when hidden
        edit_button_retain_size = self.save_button.sizePolicy()
        edit_button_retain_size.setRetainSizeWhenHidden(True)
        self.save_button.setSizePolicy(edit_button_retain_size)
        self.cancel_button.setSizePolicy(edit_button_retain_size)

        top_hbox.addWidget(self.name_label)
        top_hbox.addWidget(self.edit_options, Qt.AlignRight)

        # These widgets are all related to the time and will be in their own row
        time_edit_size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        time_row = QWidget()
        time_row_hbox = QHBoxLayout(time_row)
        start_label = QLabel("Start: ")
        self.start_time_edit = QTimeEdit(self.start_time)
        self.start_time_edit.setSizePolicy(time_edit_size_policy)
        end_label = QLabel("End: ")
        self.end_time_edit = QTimeEdit(self.end_time)
        self.end_time_edit.setSizePolicy(time_edit_size_policy)

        time_row_hbox.addWidget(start_label)
        time_row_hbox.addWidget(self.start_time_edit, Qt.AlignLeft)
        time_row_hbox.addWidget(end_label)
        time_row_hbox.addWidget(self.end_time_edit, Qt.AlignLeft)

        self.description_edit = QTextEdit()
        self.description_edit.setAcceptRichText(False)
        self.description_edit.setPlainText(self.description)

        self.vbox.addWidget(topbar)
        self.vbox.addWidget(time_row)
        self.vbox.addWidget(self.description_edit)


    def start_editing(self):
        self.editing = True # Maybe I should combine these methods to use a boolean argument instead of hard-coding everything?

        self.edit_button.hide()
        self.save_button.show()
        self.cancel_button.show()
        self.delete_button.show()

        # Enable widget editing
        self.description_edit.setReadOnly(False)
        self.start_time_edit.setReadOnly(False)
        self.end_time_edit.setReadOnly(False)

        # Adjust Styles
        self.description_edit.setFrameStyle(QFrame.Sunken | QFrame.StyledPanel)
        self.start_time_edit.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.end_time_edit.setButtonSymbols(QAbstractSpinBox.UpDownArrows)

    def stop_editing(self):
        self.editing = False

        self.save_button.hide()
        self.cancel_button.hide()
        self.delete_button.hide()
        self.edit_button.show()

        # Disable widget editing
        self.description_edit.setReadOnly(True)
        self.start_time_edit.setReadOnly(True)
        self.end_time_edit.setReadOnly(True)

        # Adjust Styles
        self.description_edit.setFrameStyle(QFrame.NoFrame)
        self.start_time_edit.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.end_time_edit.setButtonSymbols(QAbstractSpinBox.NoButtons)

    def save_changes(self):
        # NOTE Qt has something called a QValidator. Maybe I can look into that and try to use it
        start, end = self.start_time_edit.time(), self.end_time_edit.time()
        duration_secs = start.secsTo(end)
        if duration_secs < 0:
            raise ValueError("Start time should be earlier than end time")
        duration = duration_secs // 60
        start_datetime = QDateTime(self.day, start)

        description = self.description_edit.toPlainText()

        self.stop_editing()
        self.updated.emit((self.id, self.item_id, self.tags, description, start_datetime, duration, self.completed))

    def cancel_edit(self):
        self.refresh_view()
        self.stop_editing()

    def refresh_view(self):
        # Update all display widgets to show values of attributes
        self.start_time_edit.setTime(self.start_time)
        self.end_time_edit.setTime(self.end_time)
        self.description_edit.setPlainText(self.description)

    def update_data(self, start:str, duration:int, description:str, completed:Optional[bool]):
        self.day = start.date()
        self.start_time = start.time()
        self.duration = duration
        self.end_time = self.start_time.addSecs(duration * 60)
        self.description = description

        self.refresh_view()

    def paintEvent(self, paint_event):
        """ This method allows the widget to implement styles from a stylesheet
        Learned from: https://wiki.qt.io/How_to_Change_the_Background_Color_of_QWidget """

        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def time_overlap(self, schedule_item):
        """
            Compares the start and end times of self to
            another schedule Item.
            Returns an int in the range of -2 to 2, inclusive, based on the times

            Return Values:
                -2: self takes place within schedule_item
                    self.start > schedule_item.start AND self.end <= schedule_item.end

                -1: self ends during schedule_item (schedule_item starts during self)
                    self.start < schedule_item.start
                        AND self.end > schedule_item.start
                        AND self.end < schedule_item.end

                 0: the items do not overlap at any time
                    self.start >= schedule_item.end OR self.end <= schedule_item.start

                 1: schedule_item ends during self (self starts during schedule_item)
                    self.start > schedule_item.start
                        AND self.start < schedule_item.end
                        AND self.end > schedule_item.end

                2: schedule_item takes place within self
                    self.start < schedule_item.start AND self.end >= schedule_item.end
        """
        # NOTE: I can't help but feel like there is a better way to do this.
        #       Maybe I'll come back and try to simplify it.
            # For now items w/ identical times just return 0 to say they should not be nested
        if self.start == schedule_item.start and self.end == schedule_item.end:
            return 0
        if self.start > schedule_item.start:
            if self.end <= schedule_item.end:
                return -2
            elif self.start < schedule_item.end:
                return -1
            else:
                return 0
        elif self.start < schedule_item.start:
            if self.end >= schedule_item.end:
                return 2
            elif self.end > schedule_item.start:
                return 1
            else:
                return 0

# NOTE I kind of like the idea of making another base class for items that can have children.
class NestingItem(ScheduleItem):
    can_have_children = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.children = []

    def init_ui(self):
        super().init_ui()

        self.child_container = QWidget()
        self.child_vbox = QVBoxLayout(self.child_container)

        self.vbox.addWidget(self.child_container)

    def add_child(self, new_child):
        # Children should be inserted in order by their start times
        if self.time_overlap(new_child) != 2:
            raise ValueError("Child ScheduleItem must have start_time after parent's start_time and end_time before parent's end_time")
        insertion_index = None
        for child in sorted(self.children, key=lambda c: c.start_time):
            if new_child.start_time < child.start_time:
                insertion_index = self.children_vbox.indexOf(child)
                break
        if insertion_index is None:
            self.children_vbox.addWidget(new_child)
        else:
            self.children_vbox.insertWidget(insertion_index, new_child)
        new_child.parent_item = self
        self.children.append(new_child)

    def remove_child(self, child):
        self.child_vbox.removeWidget(child)
        self.children.remove(child)
        child.parent_item = None


class TimeFrame(ScheduleItem):
    """ A note is something you would like to see in your daily plan, such as a reminder """
    item_type = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class Task(ScheduleItem):
    """ A Task is something you want to do that has a definite complete state """
    item_type = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.completed = False

    def init_name(self):
        self.name_label = QCheckBox(self.name)
        self.name_label.setChecked(self.completed)
        self.name_label.clicked.connect(self.marked_complete)

    def marked_complete(self, complete):
        self.completed = complete
        self.save_changes()

class Activity(NestingItem, Task):
    """ Basically a task that can contain nested tasks """
    item_type = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

def create_schedule_item(row):
    if row['item_type'] == 0:
        return Task(row)
    elif row['item_type'] == 1:
        return TimeFrame(row)
    else:
        return ScheduleItem(row)


def main(filename):
    import db_interface as dbx
    with sqlite3.connect(filename) as con:
        con.row_factory = sqlite3.Row
        s = dbx.get_plans(con, QDate(2020, 8, 27))

    a = QApplication([])
    m = QWidget()
    m.setWindowTitle("Schedule Item Base Class")
    v = QVBoxLayout(m)
    for row in s:
        i = ScheduleItem(row)
        i.deleted.connect(lambda n: print(f"Deleted: {n}"))
        i.updated.connect(lambda n: print(f"Updated: {n}"))
        v.addWidget(i)
    m.show()
    a.exec_()
    #journal = load_journal(s)
    #return journal


if __name__ == '__main__':
    import sys
    main(sys.argv[1])
