from __future__ import annotations
import os
import sys
sys.path.append('C:/Users/shevc/Habits')

import main, tracker_classes           # type: ignore[import]
import pytest
from datetime import timedelta, date
from typing import Any

# type annotations for mypy
HabitManager: Any
CheckOffManager: Any 
Habit: Any
CheckOff: Any

@pytest.fixture
def today() -> date:
    #setting up a date for today variable so we know what to expect in returns dependent on today date
    return date(2024, 2, 26)

@pytest.fixture
def some_menu() -> dict[str, tuple[str,str]]:
    '''Returns an arbitrary menu object example'''
    menu_content = {'1': ("Option one", "1 + 10"),
                    '2': ("Option two", "20 + 10"),
                    '3': ("Option three", "300 + 10"),
                    '4': ("Option four", "-4 + 10"),
                    '5': ("Exit", "") }
    return menu_content

def test_menu_executor(monkeypatch: pytest.MonkeyPatch, 
                       some_menu: dict[str, tuple[str,str]]
                      ) -> None:
    ''' Testing menu_executor fucntion from main module by monkeypatching input.
    '''
    inputs = ('1', '2', '3', '4')
    result = [11, 30, 310, 6]
    for elem in inputs:
        # monkeypatch the "input" function
        monkeypatch.setattr('builtins.input', lambda _: elem)
        assert main.menu_executor(some_menu) == result[int(elem) - 1]
    monkeypatch.setattr('builtins.input', lambda _: '5')
    # testing exit option
    with pytest.raises(SystemExit):
        main.menu_executor(some_menu)

        
def test_add_new_habit(monkeypatch: pytest.MonkeyPatch, today: date) -> None:
    ''' Testing add_habit method of Habit Manager class. '''
    max_habit_title = 20  # max lenght of habit title
    max_habit_descr = 45  # max length of habit description
    habit_manager = tracker_classes.HabitManager("test_habit_data.json", today)

    # first "YES" test 
    monkeypatch.setattr('builtins.input', lambda _: "101")
    assert habit_manager.add_habit(max_habit_title, max_habit_descr) == True

    # test of too long habit title length
    inputs = iter(["YES", "21 chars habit title "])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    assert habit_manager.add_habit(max_habit_title, max_habit_descr) == True
    
    # test of empty habit title length
    inputs = iter(["YES", ""])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    assert habit_manager.add_habit(max_habit_title, max_habit_descr) == True
    
    # test of too short description length
    inputs = iter(["YES", "20 chars habit title", ""])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    assert habit_manager.add_habit(max_habit_title, max_habit_descr) == True
    
    # test of too long description length
    inputs = iter(["YES", "20 chars habit title", "46 chars description 46 chars description 46 c"])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    assert habit_manager.add_habit(max_habit_title, max_habit_descr) == True

    # test of wrong periodicity
    inputs = iter(["YES", "20 chars habit title", 
                   "45 chars description 45 chars description 45 ",
                   "Weekly"])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    assert habit_manager.add_habit(max_habit_title, max_habit_descr) == True
    
    # test wrong confirmation
    inputs = iter(["YES", "20 chars habit title", 
                   "45 chars description 45 chars description 45 ",
                   "1", "I need to think about it"])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    assert habit_manager.add_habit(max_habit_title, max_habit_descr) == True
    
    # test creation of correct habit
    inputs = iter(["YES", "20 chars habit title", 
                   "45 chars description 45 chars description 45 ",
                   "1", "YES"])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    habit_manager.add_habit(max_habit_title, max_habit_descr)

    result = tracker_classes.Habit("20 chars habit title", 
                                   "45 chars description 45 chars description 45 ",
                                   "Daily",
                                    today, 
                                    today,
                                    True
                                   )
    assert habit_manager.object_list[0] == result
    
    # read the JSON file to see if the record of the new habit correct
    new_habit_manager = tracker_classes.HabitManager("test_habit_data.json", today)
    new_habit_manager.make_list()
    assert new_habit_manager.object_list[0] == result
    
    # testing duplicate of title
    inputs = iter(["YES", "20 chars habit title"])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    assert habit_manager.add_habit(max_habit_title, max_habit_descr) == True
    
    # testing duplicate of description
    inputs = iter(["YES", "New habit title", "45 chars description 45 chars description 45 "])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    assert habit_manager.add_habit(max_habit_title, max_habit_descr) == True
    
    #cleaning 
    os.remove("test_habit_data.json")
    
    
@pytest.fixture
def habit_instance(today: date) -> "HabitManager":
    # creating two habits: daily and weekly to be used in further testing
    habit_manager = tracker_classes.HabitManager("test_habit_data.json", today)
    test_habit_daily = tracker_classes.Habit("Daily habit title", 
                                             "Daily habit description",
                                             "Daily",
                                              date(2024, 1, 1), 
                                              date(2024, 1, 1),
                                              True
                                             )
    habit_manager.object_list.append(test_habit_daily)
    test_habit_weekly = tracker_classes.Habit("Weekly habit title", 
                                             "Weekly habit description",
                                             "Weekly",
                                              date(2024, 1, 1), 
                                              date(2024, 1, 1),
                                              True
                                             )
    habit_manager.object_list.append(test_habit_weekly)
    habit_manager._save_list(habit_manager.object_list)
    return habit_manager
    

def test_modify_habit_description(monkeypatch: pytest.MonkeyPatch,
                                  habit_instance: "Habit",
                                  today: date
                                 ) -> None:
    '''Testing modify_description method of HabitManager class.'''
    # testing no file case
    habit_manager = tracker_classes.HabitManager("test_habit.json", today)
    assert habit_manager.modify_description() == True
    
    # testing changing description
    inputs = iter(["1", "New description"])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    habit_instance.modify_description()

    result = tracker_classes.Habit("Daily habit title", 
                                   "New description",
                                    "Daily",
                                    date(2024, 1, 1), 
                                    today,
                                    True
                                   )
    assert habit_instance.object_list[0] == result
    
    #cleaning 
    os.remove("test_habit_data.json")

def test_archive_habit(monkeypatch: pytest.MonkeyPatch, habit_instance: "Habit") -> None:
    #testing archiving a habit
    monkeypatch.setattr('builtins.input', lambda _: "1")
    habit_instance.archive_habit()
    result = tracker_classes.Habit("Daily habit title", 
                                    "Daily habit description",
                                    "Daily",
                                    date(2024, 1, 1), 
                                    date(2024, 1, 1),
                                    False
                                   )
    assert habit_instance.object_list[0] == result
    
    #cleaning 
    os.remove("test_habit_data.json")
    
@pytest.fixture
def check_off_instance(today: date) -> "CheckOffManager":
    # creating a check_off
    check_off_manager = tracker_classes.CheckOffManager("test_check_off.json", today)
    for created in (today - timedelta(days=1), today):
        test_check_off = tracker_classes.CheckOff("Daily habit title", 
                                                   5,
                                                   created, 
                                                  )
        check_off_manager.object_list.append(test_check_off)
    for created in (today - timedelta(days=7),
                    today - timedelta(days=6)
                   ):
        test_check_off = tracker_classes.CheckOff("Weekly habit title", 
                                                   5,
                                                   created, 
                                                  )
        check_off_manager.object_list.append(test_check_off)
    check_off_manager._save_list(check_off_manager.object_list)
    return check_off_manager   


def test_delete_habit(monkeypatch: pytest.MonkeyPatch,
                      habit_instance: "Habit",
                      check_off_instance: "CheckOff"
                     ) -> None:
    ''' Testing delete method of HabitManger. '''
    rest_habit = habit_instance.object_list[1]
    #testing no "YES" for the question "Are you sure?"
    inputs = iter(["1", "YE"])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    assert habit_instance.delete_habit(check_off_instance) == True
    
    inputs = iter(["1", "YES"])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    habit_instance.delete_habit(check_off_instance)
    assert habit_instance.object_list == [rest_habit]
    check_off_instance.make_list("Daily habit title")
    assert check_off_instance.object_list == [] 
    
    #cleaning 
    os.remove("test_habit_data.json")
    os.remove("test_check_off.json")
    
    
def test_report_check_off(monkeypatch: pytest.MonkeyPatch,
                      habit_instance: "Habit",
                      check_off_instance: "CheckOff",
                      today: date
                     ) -> None:
    ''' Testing report_check_off method of CheckOffManager. '''
    
    #testing attempt to check-off daily habit second time at the same date
    chosen_habit = habit_instance.object_list[0]
    assert check_off_instance.report_check_off(chosen_habit, 5) == True
    
    #deleting today check-off of daily habit 
    new_check_off_gen = (elem for elem in check_off_instance.make_gen() 
                            if elem != check_off_instance.object_list[1])
    check_off_instance._save_list(new_check_off_gen)
    
    #testing wrong emotion level
    for inputs in [-1, 6]:
        monkeypatch.setattr('builtins.input', lambda _: inputs)
        assert check_off_instance.report_check_off(chosen_habit, 5) == True
    
    #testing check-off with correct emotion level
    monkeypatch.setattr('builtins.input', lambda _: 0)
    check_off_instance.report_check_off(chosen_habit, 5)
    test_check_off = tracker_classes.CheckOff("Daily habit title", 
                                               0,
                                               today, 
                                              )
    assert check_off_instance.object_list[1] == test_check_off

    #testing attempt to check-off weekly habit second time at the same week
    chosen_habit = habit_instance.object_list[1]
    assert check_off_instance.report_check_off(chosen_habit, 5) == True
    
    #deleting this week check-off of daily habit 
    new_check_off_gen = (elem for elem in check_off_instance.make_gen() 
                            if elem != check_off_instance.object_list[1])
    check_off_instance._save_list(new_check_off_gen)
    
    #testing check-off with correct emotion level
    monkeypatch.setattr('builtins.input', lambda _: 0)
    check_off_instance.report_check_off(chosen_habit, 5)
    test_check_off = tracker_classes.CheckOff("Weekly habit title", 
                                               0,
                                               today, 
                                              )
    assert check_off_instance.object_list[1] == test_check_off
   
    #cleaning 
    os.remove("test_habit_data.json")
    os.remove("test_check_off.json")

    
def test_delete_check_off(monkeypatch: pytest.MonkeyPatch,
                          habit_instance: "Habit",
                          check_off_instance: "CheckOff"
                         ) -> None:
    ''' Testin delete_check_off method of CheckOffManager. '''
    
    rest_check_off = check_off_instance.object_list[0]
    chosen_habit = habit_instance.object_list[0]
    #testing wrong check-off number to delete
    for inputs in [0, 3]:
        monkeypatch.setattr('builtins.input', lambda _: inputs)
        assert check_off_instance.delete_check_off(chosen_habit, 5) == True
    
    #testing deleting recent check-off
    monkeypatch.setattr('builtins.input', lambda _: 2)
    check_off_instance.delete_check_off(chosen_habit, 5)
    check_off_instance.make_list(chosen_habit.title)
    assert check_off_instance.object_list == [rest_check_off]
    
    #cleaning 
    os.remove("test_habit_data.json")
    os.remove("test_check_off.json")


@pytest.mark.parametrize("test_habit, expected", 
                         [("Evening meditation", (2.0, "Negative")),
                          ("Morning meditation", (3.2, "Positive")),
                          ("Morning run", (3.4, "Negative")),
                           ("Sweaming in pool", (4.5, "Neutral"))]
                        )
def test_emotion(test_habit: str, expected: tuple[int, str], today: date) -> None:
    ''' Testing emotion fucntion of main module. '''
    check_off_manager = tracker_classes.CheckOffManager("check_off_test.json", today)
    check_off_manager.make_list(test_habit, 5)
    assert main.emotion(check_off_manager) == expected
    
   
@pytest.mark.parametrize("test_habit, expected", 
                         [("Evening meditation", (15, "Streak", 1, 0, 3, 2.0, "Negative")),
                          ("Morning meditation", (22, "Streak", 1, 0, 2, 3.2, "Positive")),
                          ("Morning run", (18, "Streak", 4, 0, 4, 3.4, "Negative")),
                          ("Evening yoga", (3, "Broken", 0, 3, 1, "N/D", "N/D")),
                          ("Sweaming in pool", (3, "Streak", 1, 0, 2, 4.5, "Neutral")),
                          ("Not started habit", (11, "Not started", 0, 0, 0, "N/D", "N/D"))]
                        )
def test_streak(test_habit: str, 
                expected: tuple[int, str, int, int, int, float, str],
                today: date
               ) -> None:
    ''' Testing streak function from main module. '''
    habit_manager = tracker_classes.HabitManager("habit_data_test.json", today)
    check_off_manager = tracker_classes.CheckOffManager("check_off_test.json", today)
    habit_manager.make_list()
    habit = [x for x in habit_manager.object_list if x.title == test_habit]
    assert main.streak(*habit, check_off_manager, 5, today) == expected                 
