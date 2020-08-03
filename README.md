Day Builder
-----------
Day Builder is a simple daily planning program.
This program is focused on the importance of making concrete plans
each day, saving your future self the time and energy required to
make decisions in the moment.
It also lets you quickly review your history and shows statistics
that can help you find ways to improve your day.

Written in Python 3.8
Dependencies: PyQt5, numpy, pandas

This is still a work in progress and I will update the readme in the future.

Important
---------
I'm still learning how to structure a project like this and how to handle
custom packages and modules.

Currently you need to run the python programs as modules by using the -m flag.
In order to get the daybuilder application to run you need to be in the top-level daybuilder directory and enter the command

    python3 -m daybuilder.daybuilder [relative path to database separated by spaces] [database file]
    - if you provide no arguments the program will create a default database
      'data/my.db' in the same directory as daybuilder.py

The next thing I want to do is make this more pleasant

Credit
------
I use some of the icons from the Silk icons pack as backup icons.
  - Silk Icons (http://www.famfamfam.com/lab/icons/silk/)
