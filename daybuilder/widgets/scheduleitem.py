""" Module containing classes for schedule items and functions
    that make it easy to work with them """

from datetime import date, datetime, time, timedelta
from daybuilder.utils import db_interface, util
import logging
from PyQt5.QtCore import QSize, pyqtSignal, Qt
from PyQt5.QtGui import QBrush, QPalette, QColor, QPainter
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton, QCheckBox, QTextEdit, QFrame, QStyleOption, QStyle, QVBoxLayout, QTimeEdit, QMessageBox, QSizePolicy, QHBoxLayout

class ScheduleItem(QWidget):
    item_type = None
    updated = pyqtSignal(tuple)
    deleted = pyqtSignal(int)

    def __init__(self, row, *args, **kwargs):
        super(ScheduleItem, self).__init__(*args, **kwargs)
        self.setProperty("qclass", "schedule-item")
        self.setAutoFillBackground(True)
        # Load item info
        self.id = row['active_id']
        self.item_id = row['item_id']
        self.description = row['description']
        self.tags = []
        day = datetime.fromisoformat(row['start'])
        self.date = day.date()
        self.start = day.time()
        self.end = (day + timedelta(minutes=row['duration'])).time()
        self.duration = row['duration']
        self.completed = row['completed']
        # Create subwidgets
        self.grid = QGridLayout(self)
        self.editing = False
        edit_container = QWidget()
        self.edit_controls = QHBoxLayout(edit_container)
        self.edit_button = QPushButton(icon=util.edit_icon(), text="Edit")
        self.save_button = QPushButton(icon=util.save_icon(), text="Save")
        self.cancel_button = QPushButton(icon=util.cancel_icon(), text="Undo")
        self.delete_button = QPushButton(icon=util.delete_icon(), text="Delete")
        self.edit_button.clicked.connect(self.start_editing)
        self.save_button.clicked.connect(self.save_edit)
        self.cancel_button.clicked.connect(self.cancel_edit)
        self.delete_button.clicked.connect(self.confirm_deletion)
        self.edit_controls.addWidget(self.save_button)
        self.edit_controls.addWidget(self.cancel_button)
        self.edit_controls.addWidget(self.edit_button)
        self.edit_controls.addWidget(self.delete_button)
        retain_policy = self.save_button.sizePolicy()
        retain_policy.setRetainSizeWhenHidden(True)
        self.save_button.setSizePolicy(retain_policy)
        self.cancel_button.setSizePolicy(retain_policy)

        self.start_label = QLabel(f"{self.start.strftime('%I:%M %p')}")
        self.time_label_separator = QLabel("to")
        self.end_label = QLabel(f"{self.end.strftime('%I:%M %p')}")
        self.start_time_edit = QTimeEdit(self.start)
        self.end_time_edit = QTimeEdit(self.end)
        if self.duration == 0:
            self.time_label_separator.hide()
            self.end_label.hide()
        self.desc_box = QTextEdit()
        # I am doing this so newlines actually work.
        # But rich text could be interesting. Maybe I can make it an option.
        self.desc_box.setAcceptRichText(False)
        self.desc_box.setPlainText(row['description'])
        self.desc_box.setFrameStyle(QFrame.NoFrame)
        self.desc_box.setReadOnly(True)
        # Set grid
        self.grid.addWidget(self.start_label, 0, 1)
        self.grid.addWidget(self.time_label_separator, 0, 2)
        self.grid.addWidget(self.end_label, 0, 3)
        self.grid.addWidget(self.start_time_edit, 0, 1)
        self.grid.addWidget(self.end_time_edit, 0, 3)
        self.start_time_edit.hide()
        self.end_time_edit.hide()
        self.grid.addWidget(self.desc_box, 1, 0, 1, 5)
        self.grid.addWidget(edit_container, 0, 4)

        self.save_button.hide()
        self.cancel_button.hide()
        self.delete_button.hide()
        self.grid.setRowMinimumHeight(1, 64)
        self.grid.setRowStretch(1, 2)
        self.grid.setAlignment(edit_container, Qt.AlignRight)

        self.start_label.setSizePolicy(QSizePolicy(0, 0))
        self.end_label.setSizePolicy(QSizePolicy(0, 0))
        self.time_label_separator.setSizePolicy(QSizePolicy(0, 0))
        self.start_label.setProperty("font-class", "heading")
        self.end_label.setProperty("font-class", "heading")
        self.time_label_separator.setProperty("font-class", "sub-heading")

        if self.desc_box.toPlainText() == "":
            self.desc_box.hide()

        self.setStyleSheet("QLabel{text-align: center;}")

    def start_editing(self):
        self.setFocus()
        self.edit_button.hide()
        self.save_button.show()
        self.cancel_button.show()
        self.delete_button.show()
        self.start_label.hide()
        self.end_label.hide()
        self.time_label_separator.show()
        self.start_time_edit.show()
        self.end_time_edit.show()
        if self.desc_box.isHidden():
            self.desc_box.show()
        self.desc_box.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        #self.desc_box.setLineWidth(2)
        self.desc_box.setReadOnly(False)
        # Code that enables editing on all sub-widgets
        self.editing = True

    def stop_editing(self):
        self.setFocus()
        self.edit_button.show()
        self.save_button.hide()
        self.cancel_button.hide()
        self.delete_button.hide()
        self.start_label.show()
        if self.duration != 0:
            self.end_label.show()
        else:
            self.end_label.hide()
            self.time_label_separator.hide()
        self.start_time_edit.hide()
        self.end_time_edit.hide()
        if self.desc_box.toPlainText() == "":
            self.desc_box.hide()
        self.desc_box.setFrameStyle(QFrame.NoFrame)
        self.desc_box.setReadOnly(True)
        # Code that disables editing on all sub-widgets
        self.editing = False

    def update_data(self):
        new_start = self.start_time_edit.time()
        new_end = self.end_time_edit.time()

        if self.start > self.end:
            return False

        self.description = self.desc_box.toPlainText()
        self.tags = []
        self.start = time(new_start.hour(), new_start.minute())
        self.end = time(new_end.hour(), new_end.minute())
        self.duration = int(new_start.secsTo(new_end) // 60)
        new_datetime = datetime.combine(self.date, self.start)

        self.update_display()

        self.updated.emit((self.id, self.item_id, self.tags,
                            self.description,
                            new_datetime, self.duration,
                            self.completed))
        return True

    def update_display(self):
        self.start_label.setText(f"{self.start.strftime('%I:%M %p')}")
        self.end_label.setText(f"{self.end.strftime('%I:%M %p')}")
        if self.duration:
            self.time_label_separator.show()
            self.end_label.show()
        else:
            self.time_label_separator.hide()
            self.end_label.hide()
        #if self.duration != 0:
        #    self.time_label_separator.show()
        #    self.end_label.show()
        #else:
        #    self.time_label_separator.hide()
        #    self.end_label.hide()


    def restore_data(self):
        self.desc_box.setText(self.description)
        self.start_time_edit.setTime(self.start)
        self.end_time_edit.setTime(self.end)

    def save_edit(self):
        if not self.update_data():
            msg = QMessageBox()
            msg.warning(self, "Invalid Info", "Start time should be earlier than End time")
            return
        self.update_display()
        self.stop_editing()

    def cancel_edit(self):
        self.restore_data()
        self.stop_editing()

    def confirm_deletion(self):
        """Function that verifies you really want to delete the item.
            Maybe I can make an option that disables this if I am not
            worried about accidentally deleting something. """
        message_text = f"You are about to delete your scheduled item\n" + \
                f"    '{self.name.text()}' at {self.start.strftime('%I:%M %p')}" + \
                f" on {self.date.strftime('%m/%d/%y')}\n" + \
                       "Are you sure?"
        msg = QMessageBox()
        response = msg.question(self, "Delete Scheduled Item", message_text)

        if response == QMessageBox.Yes:
            self.deleted.emit(self.id)

    def overlaps(self, item):
        if self.start < item.end and self.end > item.start:
            return True
        return False

    def paintEvent(self, paint_event):
        """
            I needed to override the paintEvent method in order to get
            these custom widgets to draw their backgrounds.
            https://wiki.qt.io/How_to_Change_the_Background_Color_of_QWidget
        """
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)

    def __repr__(self):
        return f"{self.__class__.__name__}({str(self.__dict__)})"


class Task(ScheduleItem):
    item_type = 0
    def __init__(self, row, *args, **kwargs):

        self.name = QCheckBox(row['item_name'])
        self.name.setProperty("font-class", "content")
        # NOTE: I would like to change the way I save changes to the database.
        # The ScheduleItem.update signal causes the DailyPlanner widget
        # to call the ScheduleItem.update_db method on each ScheduleItem
        # in the given day. This feels wasteful. Currently the DailyPlanner
        # needs to call update_db because it provides the connection to the db.
        self.name.stateChanged.connect(lambda x: self.updated.emit((self.id, self.item_id, self.tags,
                            self.description,
                            datetime.combine(self.date, self.start),
                            self.duration, self.completed)))
        # Since this class defines completed to be a property which uses
        # self.name, I have to initialize self.name before executing
        # the ScheduleItem's init, as that method accesses the completed
        # property.
        super(Task, self).__init__(row, *args, **kwargs)
        self.grid.addWidget(self.name, 0, 0)
        self.setProperty("type", "task")
        self.setAutoFillBackground(True)

    @property
    def completed(self):
        return self.name.isChecked()

    @completed.setter
    def completed(self, complete):
        self.name.setChecked(complete)

    def __str__(self):
        """ Temporary method formatted for a crude canvas """
        string = f"{self.start.strftime('%H:%M')} : {self.item_name}\n"
        if self.description:
            string += f"  {self.description}\n"
        string += f"  COMPLETED: {bool(self.completed)}"
        return string


class Timeframe(ScheduleItem):
    item_type = 1

    def __init__(self, row, *args, **kwargs):
        super(Timeframe, self).__init__(row, *args, **kwargs)
        self.task_container = QWidget()
        self.task_vbox = QVBoxLayout(self.task_container)

        self.name = QLabel(row['item_name'])
        self.name.setProperty("font-class", "content")

        self.grid.addWidget(self.name, 0, 0)
        self.grid.addWidget(self.task_container, 2, 1, 1, 6)
        self.setProperty("type", "timeframe")
        self.setAutoFillBackground(True)

    def add_task(self, task):
        self.task_vbox.addWidget(task)
        # I want it to round up more often
        stretch = round((task.duration + 10) / 60)
        self.task_vbox.setStretch(self.task_vbox.indexOf(task), stretch)


class Reminder(ScheduleItem):
    item_type = 2
    pass


def get_item(row):
    # Take dictionary returned by the db_interface schedule function
    # and use the item_type field to determine which class to use.
    if row['item_type'] == 0:
        return Task(row)
    elif row['item_type'] == 1:
        return Timeframe(row)


