from daybuilder.widgets import dailyplanner, stats_view, history_view
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QStackedLayout, QWidget, QPushButton, QTabWidget
import os
import sys

#Globals
# Colors for the buttons in the nav bar
HIGHLIGHT_COLOR = '#3232CC'
DEFAULT_COLOR = '#242436'

class DayBuilder(QWidget):
    def __init__(self, database, *args, **kwargs):
        super(DayBuilder, self).__init__(*args, **kwargs)
        self.database = database
        self.setProperty("id", "daybuilder")
        self.setWindowTitle("Day Builder")
        self.vbox = QVBoxLayout(self)

    def init_widgets(self):
        self.nav = QTabWidget()
        self.nav.setProperty("id", "nav")
        self.vbox.addWidget(self.nav)

        self.dailyplanner = dailyplanner.DailyPlanner(self.database)
        self.history = history_view.HistoryView(self.database)
        self.stats = stats_view.StatsView(self.database)

        self.nav.addTab(self.dailyplanner, "&Daily Planner")
        self.nav.addTab(self.stats, "&Statistics")
        self.nav.addTab(self.history, "&History")

        self.nav.currentChanged.connect(self.reload_page)

    def reload_page(self, page_number):
        if page_number == 1:
            self.stats.refresh()
        elif page_number == 2:
            self.history.set_view()

    def raise_history(self):
        """ Set the history view as the main content,
        and refresh the data since it might have been changed"""
        self.main_stack.setCurrentWidget(self.history)
        self.history.set_view()
        self.set_highlight(self.open_history)

    def raise_stats(self):
        """ Set the statistics view as the main content and 
        refresh the data """
        self.main_stack.setCurrentWidget(self.stats)
        self.stats.refresh()
        self.set_highlight(self.open_stats)

def main(args):
    if len(args) > 1:
        if args[1] == '-t':
            path = ["tests", "data", "randy.db"]
        else:
            path = args[1:]
    else:
        # TODO: make it so the user can choose a default file
        default_db = "my.db"
        path = ["data", default_db]
    db = os.path.join(os.path.dirname(__file__), *path)

    if not os.path.exists(db):
        from daybuilder.utils import init_db
        init_db.main(db)

    app = QApplication([])
    daybuilder = DayBuilder(db)
    daybuilder.show()
    daybuilder.init_widgets()
    with open(os.path.join(os.path.dirname(__file__), "daybuilder_styles.qss")) as styles:
        daybuilder.setStyleSheet(styles.read())
    app.exec_()


if __name__ == '__main__':
    main(sys.argv)
