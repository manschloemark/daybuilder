from datetime import date
from daybuilder.utils import util
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QRadioButton, QButtonGroup, QPushButton, QStackedLayout, QGroupBox

class DailyRating(QWidget):
    """
    Widget that will be used to ask the user to rate their
    days on a scale of 1 to 5
    """
    submit = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super(DailyRating, self).__init__(*args, **kwargs)
        #self.stack = QStackedLayout(self)

        #self.start_button = QPushButton("Rate Day")
        #self.start_button.clicked.connect(lambda x: self.stack.setCurrentWidget(self.selection))

        #self.selection = QWidget()
        #self.vbox = QVBoxLayout(self.selection)
        self.vbox = QVBoxLayout(self)

        self.choice_container = QGroupBox("How was your day?")
        self.choice_hbox = QHBoxLayout(self.choice_container)
        self.choices = QButtonGroup()
        for key, value in util.rating_value_map.items():
            if key == None:
                continue
            rating = QRadioButton(text=value)
            self.choices.addButton(rating)
            self.choices.setId(rating, key)
            self.choice_hbox.addWidget(rating)

        #button_container = QWidget()
        #button_hbox = QHBoxLayout(button_container)
        #self.confirm_button = QPushButton("Confirm")
        #self.confirm_button.clicked.connect(self.confirm)
        #self.cancel_button = QPushButton("Cancel")
        #self.cancel_button.clicked.connect(self.cancel)

#        button_hbox.addWidget(self.confirm_button)
#        button_hbox.addWidget(self.cancel_button)

        self.vbox.addWidget(self.choice_container)
        #self.vbox.addWidget(button_container)

        #self.stack.addWidget(self.start_button)
        #self.stack.addWidget(self.selection)

#    def confirm(self):
#        rating = self.choices.checkedId()
#        if rating == -1:
#            return
#        self.choices.checkedButton().setChecked(False)
#        self.submit.emit(rating)
#        self.stack.setCurrentWidget(self.start_button)
#
#
#    def cancel(self):
#        if self.choices.checkedButton():
#            self.choices.checkedButton().setChecked(False)
#        self.stack.setCurrentWidget(self.start_button)

    def refresh(self, rating, day):
        if rating:
            if day > date.today():
                self.choice_container.setTitle("Predicted Rating")
            else:
                self.choice_container.setTitle("Daily Rating")
            self.choices.button(rating).setChecked(True)
        else:
            if self.choices.checkedButton():
                # You cannot uncheck a radio button while
                # their QButtonGroup is set to exclusive
                self.choices.setExclusive(False)
                self.choices.checkedButton().setChecked(False)
                self.choices.setExclusive(True)
            if day > date.today():
                self.choice_container.setTitle("Predict a rating")
            else:
                self.choice_container.setTitle("Pick a rating")

