""" Module containing useful variables and functions used in multiple
    other modules """

from PyQt5.QtGui import QIcon
import os

item_types = {0: "Task", 1: "Timeframe",}
rating_value_map = {None: "N/A", 1: "Terrible", 2: "Bad", 3: "Okay", 4: "Good", 5: "Amazing"}
rating_color_map = {
        None: "#646464",
        1: "#8e0501",
        2: "#d94008",
        3: "#d0952f",
        4: "#8f9325",
        5: "#52711e"
    }
weekday_map = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"}
# Icons
# Apparently these icons only work in GNOME and KDE
# So I set fallback icons from the free Silk icon set
# link: http://www.famfamfam.com/lab/icons/silk/
# ok so I'm making these functions because I was getting an error
# saying 'Must construct a QGuiApplication before a QPixMap
def edit_icon():  return QIcon.fromTheme("edit", QIcon(os.path.join("backup_icons", "note_edit.png")))
def save_icon(): return QIcon.fromTheme("document-save", QIcon(os.path.join("backup_icons", "disk.png")))
def cancel_icon(): return QIcon.fromTheme("document-revert", QIcon(os.path.join("backup_icons", "arrow_undo.png")))
def delete_icon(): return QIcon.fromTheme("edit-delete", QIcon(os.path.join("backup_icons", "cancel.png"))) # cancel icon is being used as delete intentionally
def back_icon(): return QIcon.fromTheme("media-seek-backward", QIcon(os.path.join("backup_icons", "arrow_left.png")))
def forward_icon(): return QIcon.fromTheme("media-seek-forward", QIcon(os.path.join("backup_icons", "arrow_right.png")))
def new_date_icon(): return QIcon.fromTheme("appointment-new", QIcon(os.path.join("backup_icons", "calendar.png")))
