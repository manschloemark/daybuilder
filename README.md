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

I would like to rebuild the program from scratch.<br>My main goal is to simplify the repository and use some of Qt's features that I didn't even know about at the start.<br>There are also a lot of design decisions that I want to reconsider now that I have had some time to use the application as part of my daily routine.
Here are some things I will be working on:
  - Add keyboard shortcuts
    - I would like this program to be fully usable without a mouse.
    - The program should be fast and responsive enough to make keyboard commands more efficient than using a mouse
  - Use more features from Qt to simplify the code
  - Add User Preferences
    - Set default save locations
    - Customize appearance
  - Improve Daily Planning feature
    - Add a new type of schedule item called 'Activities' that are tasks with sub-tasks
    - Make it easier to delete / update multiple tasks
    - take notes about the day during the day and compare them to your plans
    - 'Pomodoro' / Automatic Break feature that will add breaks to your plans at regular customizable intervals
  - Learn more about Pandas and add more statistics
  - Simplify the code base / choose better names for things
  - Make it easier to run the program

## Credit
I use the Silk icons pack when the user does not have any Qt themes.
  > Silk Icons (http://www.famfamfam.com/lab/icons/silk/)
