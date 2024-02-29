from __future__ import annotations
from tracker_classes import HabitManager, CheckOffManager, Habit, CheckOff
import numpy as np
from datetime import timedelta, date, datetime
from typing import Union, Optional, Callable, Any
from tabulate import tabulate
import itertools, functools


def menu_executor(content: dict[str, Any]) -> Union[Callable[[str], Any], bool]:
    ''' Function to print menu, collect the choice of the user and perform the command line
        corresponding to the chosen menu option. It receives a dict with options and command
        lines (menu instances).
        
        In case not existant option is chosen, fucntion returns "True" to be used in the calling
        menu fucntion to start again a "while loop". 
    '''
    options = content.keys()
    for entry in options: 
        print(f"{entry}. {content[entry][0]}")
    choice = input("Please Select:")
    if choice == list(content.keys())[-1]:          # last choice in menu always is Exit
        print("Good bye!")
        raise SystemExit
    elif choice in list(content.keys())[:-1]:
        return eval(content[choice][1])
    else:
        print(f"ValueError: Input is not in range from 1 to {list(content.keys())[-1]}.")
        return True


def main_menu() -> None:
    ''' This is the first menu to be printed after the program started. User can choose among 
        three sub-menus: manipulations with check-offs, habits and dashboard for habits analysis.
        
        "While loop" is used to start over the menu when exectutor returns True. This happens always
        no matter action is performed well or was aborted on the way because of some mistake. 
        This we user can stay in the program any time untill decides to choose exit option or close
        the program window.
    '''
    print("Main menu")
    menu_content = {'1': ("Check-offs", "check_off_menu()"),
                    '2': ("Habits", "habit_menu()"),
                    '3': ("Dashboard", "dashboard_menu()"),
                    '4': ("Exit", "")
                    }
    while menu_executor(menu_content):
        pass


def check_off_menu() -> None:
    ''' This is a check-off menu leading to tow main operations with check-offs: 
        (1) report a new check-off for a given habit, 
        (2) delete check-off reported by mistake.
        This is done by calling a function check_off().
    '''
    print("Check-off menu")
    menu_content = {'1': ("Report check-off", "check_off(\"report\")"),
                    '2': ("Delete check-off", "check_off(\"delete\")"),
                    '3': ("Return to main menu", "main_menu()"),
                    '4': ("Exit", "")
                   }
    while menu_executor(menu_content):
        pass        


def habit_menu() -> None:
    ''' Habit menu offers four options concerning habits: 
        (1) add a new habit, calls method HABIT_MANAGER.add_habit,
        (2) modify habit description, calls HABIT_MANAGER.modify_description,
        (3) archive habit, calls HABIT_MANAGER.archive_habit,
        (4) delete habit, calls HABIT_MANAGER.delete_habit.
       
    '''
    print("Habit menu")
    menu_content = {'1': ("Add new habit", "HABIT_MANAGER.add_habit(MAX_HABIT_TITLE, MAX_HABIT_DESCR)"),
                    '2': ("Modify habit description", "HABIT_MANAGER.modify_description()"),
                    '3': ("Archive habit", "HABIT_MANAGER.archive_habit()"),
                    '4': ("Delete habit", "HABIT_MANAGER.delete_habit(CHECK_OFF_MANAGER)"),
                    '5': ("Return to main menu", "main_menu()"),
                    '6': ("Exit", "")
                   }
    while menu_executor(menu_content):
        pass

        
def dashboard_menu() -> None:
    ''' This menus if for checking some analytics data oven the active and archived habits.
        It calls corresponding fucntions: dashboard_active and dashboard_archived.
    '''
    print("Dashboard menu")
    menu_content = {'1': ("Active habits", "dashboard_active()"),
                    '2': ("Archived habits", "dashboard_archived()"),
                    '3': ("Return to main menu", "main_menu()"),
                    '4': ("Exit", "")
                   }
    while menu_executor(menu_content):
        pass


def check_off(action: str) -> Optional[bool]:
    ''' This function asks user to choose a habit which check-offs they want to process.
        Then calls CHECK_OFF_MANAGER.report_check_off method to process new check-off and
        CHECK_OFF_MANAGER.delete_check_off to delete check-off.
        
        In the end it starts again check_off_menu.
    '''
    chosen_habit = HABIT_MANAGER.choose_habit()
    if not chosen_habit: return True
    if action == "report": 
        return CHECK_OFF_MANAGER.report_check_off(chosen_habit, PRINT_NUMBER)
    elif action == "delete": 
        return CHECK_OFF_MANAGER.delete_check_off(chosen_habit, PRINT_NUMBER)
    return None
    
def dashboard_active() -> None:
    ''' This is a fucntion printing a table with habits thier descriptive statistics.
        Statistics are generated by calling "streak" function. Print is done using 
        "tabulate" module. 
    '''
    result = [['Habit', 'Type', 'Per old', 'Status', 'Streak', 'Missed per',
               'Max streak', 'Aver emo', 'Emo trend']]
    all_habits = HABIT_MANAGER.make_gen()   
    for habit in all_habits:
        line = [habit.title, habit.periodicity]
        line += [*streak(habit, CHECK_OFF_MANAGER, ANALYSIS_INSTANCES, TODAY)]          
        result.append(line)
    if len(result) > 1:
        table = tabulate(result, headers='firstrow')
        print(table)
    else: print("There is no active habits registered. Register first one.")
    dashboard_menu()
    

def streak(habit: Habit, 
           check_off_manager: CheckOffManager,
           analysis_instances: int,
           today: date
          ) -> tuple[Any, ...]:
    ''' This function calucaltes all statistics to be printed in the dashboard fucntions 
        (active and archived). 

        Arguments are global constants, which could be used directy, but it does not seem 
        in a functional programming style.
        
        Fucntion start with definition of a period for Daily and Weekly habit used to identify
        streaks. Also "per_old" statistics is calculated showing how habit description is old 
        in number of periods. This is useful to decide if it is time to change something in the
        habit goal, for example.
        
        Then current streak, maximum streak in the history, status ("Streak", "Broken", "Not
        started", number of missed periods, average emotions and emotion trend are calculated 
        and returned.
    '''
    
    if habit.periodicity == "Daily": 
        period = timedelta(days=1)
    elif habit.periodicity == "Weekly": 
        period = timedelta(days=7)
    per_old = (today - habit.descr_update) // period   # how many periods habit is old
    
    # creating a list of check-offs for a given habit
    check_off_manager.make_list(habit.title)
    
    # new habit without check-offs
    if len(check_off_manager.object_list) == 0: 
        return per_old, "Not started", 0, 0, 0, "N/D", "N/D"
    
    # To calculate current streak and max_streak in the histry we generator of 
    # sequence of check-offs shifted on one instance and zipped, so that we can 
    # check if a period between two check-offs is in  period (1 for "Daily" 
    # or 7 days for "Weekly" habits). This allows functional approach to the
    # process with less stateful variables.  
    
    source = check_off_manager.make_gen(habit.title)
    bingo_str = "".join(bingo(period, elem) for elem in source) 
    #reversing the string: stating from recent
    bingo_str = bingo_str[::-1]   
    pattern = "1"
    while bingo_str.find(pattern) != -1:
        #checking if there is a streak (two or more timely check-offs) in the beggining of sequence
        if bingo_str.find(pattern) == 0: streak = len(pattern) + 1     
        pattern += "1"
    max_streak = len(pattern)
    if check_off_manager.object_list[-1].created >= today - period:
        status = "Streak"
        missed = 0
        #case: no streak in the beggining of sequence, but recent checkoff was in time
        if "streak" not in locals(): streak = 1    
    else:
        missed_time = today - timedelta(days=1) - check_off_manager.object_list[-1].created
        missed = int(round(missed_time/period,1))
        status = "Broken"
        streak = 0
    check_off_manager.make_list(habit.title, analysis_instances)  #making truncated list for emotion
    return per_old, status, streak, missed, max_streak, *emotion(check_off_manager)
    
    
def bingo(period: timedelta, chunk: tuple["CheckOff", "CheckOff"]) -> str:
    ''' Returns "1" if period between tow adjacent check-offs is less or equal to 1 day
        for Daily habits and 7 days for Weekly. Zero otherwise. These returns used to 
        build a string by streak fucntion to count streaks.
    '''
    if chunk[1].created - chunk[0].created <= period:
        return "1"
    else: 
        return "0"


def emotion(check_off_manager: "CheckOffManager") -> Union[tuple[float, str], tuple[str, str]]:
    ''' Returns average emption level and trend for the given sequence of check-offs.
        To calculate trend polyfit function from numpy module is used. This is linear
        regression. We use slope coefficient sign to set the trend to "Negative" 
        (negative slope sign), "Neutral" or "Positive". 
    '''
    
    if len(check_off_manager.object_list) < 2: return "N/D", "N/D"
    data = [element.emotion for element in check_off_manager.object_list]
    time_range = np.arange(0, len(data))
    array_data = np.array(data)
    result = np.polyfit(time_range, array_data, 1)
    if round(result[0], 1) > 0: trend = "Positive"
    elif round(result[0], 1) == 0: trend = "Neutral"
    else: trend = "Negative"
    return round(sum(data)/len(data), 1), trend     # return average emotion and trend


def dashboard_archived():
    ''' This function builds a table of archived habits with two statistics: Max Streak
        and Average Emotion, calculated by streak fucntion. It is not supposed to be 
        used very often, otherwise it is possible to calculate statistics once in the
        moment of archiving and store them in Habit objects to avoid extra calculations.
    '''
    result = [['Habit', 'Type', 'Description', 'Max streak', 'Aver emo']]
    all_habits = HABIT_MANAGER.make_gen(archived=True)   
    for habit in all_habits:
        line = [habit.title, habit.periodicity, habit.description]
        line += [streak(habit, CHECK_OFF_MANAGER, ANALYSIS_INSTANCES, TODAY)[4]] + \
                [emotion(CHECK_OFF_MANAGER)[0]]       
        result.append(line)
    if len(result) > 1: 
        table = tabulate(result, headers='firstrow')
        print(table)
    else: print("There is no archived habits.")
    dashboard_menu()
    

if __name__ == "__main__":
    # setting up some global parameters
    PRINT_NUMBER = 5        # number recent check-offs to print
    MAX_HABIT_TITLE = 20    # max lenght of habit title for nice table print
    MAX_HABIT_DESCR = 45    # max length of habit description for nice table print
    ANALYSIS_INSTANCES = 5  # number of instances to analyse for emotion function
    TODAY = date.today()    # today date used for creating and modifying objects
    
    # creating two main classes instances to use their methods
    HABIT_MANAGER = HabitManager("habit_data.json", TODAY)
    CHECK_OFF_MANAGER = CheckOffManager("check_off.json", TODAY)
    main_menu()