# Day Builder

Day Builder is a daily planner designed to help you visualize your day ahead of time and reflect on past days.

Made in Python using sqlite3, PyQt5, and Pandas

## Features

### Daily Planner
- View your plans and make new plans on the daily planner tab
![View of the daily planner](./examples/dailyplanner.png)
- Click 'New Plan' or any of the buttons in the 'Quick Reuse' section to open the 'New Task Form'
![Adding a new plan](./examples/new-task.png)
- schedule tasks or timeframes for specific dates and times
  - tasks are like TODO's, things you want to do. They can be marked as complete by clicking the checkbox.
  - timeframes are items you can plan that visually contain tasks whose times overlap with them.
- rate your days on a scale from 1 to 5
- quickly reuse tasks or timeframes by using the Quick Reuse sidebar.
  - Ensures that your naming is consistent and the stats are correct.


### Statistics
- as you build schedules and rate days the program will be able to calculate various statistics from your history
- gives you an opportunity to view your habits and routines empirically
![Stats screen displays overall stats about task comletion and day ratings](./examples/stats.png)

### History
- view a quick summary of your past days in a weekly and monthly format
![History view in weekly format](./examples/weekly-history.png)
![History view in monthly format](./examples/monthly-history.png)

## TODO

I am happy with the program itself but I did not write it in a way that is pleasant to read or maintain.
My understanding of Qt has grown a lot since finishing this project and I realize now that I did not use all of the
tools Qt provides.
Some day I would like to rewrite this program but I don't have the time to justify it at the moment.

## Credit
I use the Silk icons pack when the user does not have any Qt themes.
  > Silk Icons (http://www.famfamfam.com/lab/icons/silk/)
