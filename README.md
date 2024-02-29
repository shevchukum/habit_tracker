# Overview
This app tracks habits and helps to increase habit lifespan.

Problem to solve: it’s rather hard for people to maintain and develop new habits after  initial implementation.

Problem reason: with repetition new habit quickly loses dopamine kick.

Our solution: track user’s emotional level after each habit realization to alarm them if it’s trending down, so that they could introduce changes to the habit before “thrill is gone”.

For example, instead of just running for 20 min around the block every morning (which can quickly become boring), users can run in the park or find a running buddy or mix it with biking. This should increase emotional level for a while and a chance to continue running longer.

# Installation and usage
1. copy main.py and tracker_classes.py on your machine,
2. have latest version of Python installed,
3. open terminal and cd to the folder where main.py is,
4. type in the command line: python main.py.

You should see a simple menu:

![tracke_menu](https://github.com/shevchukum/habit_tracker/assets/161697125/43ec6f78-ee33-4c89-845c-0876b29fde02)

Start with registering a new habit in Habits menu. You can also modify description, archive and delete habits there.
Once you have a habit, you can check it off in Check-offs menu each time you complete it. For example, each time you come from a morning run. You will also report your emotional level form 0(low) to 5(high) with each check-off. But don't try to check-off the daily habit twice in the same day and weekly - within 3 days.

After you have at least 2 check-offs you can review full habit statistics in Dashboard.

![tracker_stats](https://github.com/shevchukum/habit_tracker/assets/161697125/b34a7141-5c12-4436-9abd-1c78725f77a1)

1. Per old - how many periods (days or weeks depending on the type of the habit: daily or weekly) ago description of the habit was changed.
2. Status: "Not started" if no check-offs yet, "Streak" if the last check-off was in the period of the habit, "Broken" if one or more periods missed.
3. Streak - how long is current streak in periods.
4. Missed per - how many full periods (days or weeks) missed if the habit is broken.
5. Max streak length in periods in the history of this habit.
6. Average emotion over the last (by default 5) periods from 0 to 5.
7. Emo trend is a slope sign of the regression over the last (5) periods. Negative means emotions are trending down and may be it's time to change something.

App will create and update two JSON files: habit_data.json for habit data and check_off.json for check-off data in the same folder with main.py.

# Configuration
In the end of main.py you can find the list of global constants and change them if needed, as well as JSON file names for storing habit and check-off data.

![tracker_config](https://github.com/shevchukum/habit_tracker/assets/161697125/b4d42ea5-23e7-47fd-a158-e8c83427a55b)


