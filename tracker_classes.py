# This module build classes: Habit, CheckOff, HabitList and CheckOffList.

from __future__ import annotations
import simplejson as json
from dataclasses import dataclass, asdict
from typing import Union, Optional, Any, Iterable
from datetime import date, timedelta, datetime
from re import match
from tabulate import tabulate
import itertools
import os


def serialize(cls: type[Any]) -> type[Any]:
    ''' Both Habit and CheckOff objects should be serialized before saved to JSON,
        this is not trivial because both of them have date variables. This decorator 
        adds a serilaization method to a class, converting not (int, str or bool) to str.
    '''
    def serialize(self) -> dict[str, Any]:
        result = {}
        for key, value in asdict(self).items():
            if not isinstance(value, (int, str, bool)):
                value = str(value)
            result[key] = value
        return result

    setattr(cls, 'serialize', serialize)
    return cls


@serialize
@dataclass(frozen=True, order=True)
class Habit:
    '''
        Represents a habit user wants to implement.
        Initialized with 
        : param title: str title of the habit,
        : param description: str detailed description of the habit, like what to do, how long ... 
        : param periodicity: str - "Daily" or "Weekly"
        : param created: date - date of habit creation
        : param descr_update: date - date of decription update, for example, new goal
        : param active: bool - False to stop tracking habit (not in the list for check-off), 
                               but keep the history available for analysis
    
        new_habit = Habit("Morning run", "Run at 9 am minimum 15 min around the block", "Daily", today, today)
    
        Note: "today" could be by default data.today(), but then it will be impossible to test
        the module with a fixed today date. I did not find the way to monkeypath datetime outside the test module.
    
        @dataclass decorator makes the class frozen to any changes after creation, works like NamedTuple. 
        Option "order" makes a sequence of Habits sortable.
        @serialize adds a method for serialization before writing down to JSON.
    '''
    
    title: str
    description: str
    periodicity: str
    created: date
    descr_update: date
    active: bool = True
    
    def __repr__(self):
        result = f"Habit details\n" \
                 f"Title: {self.title}\n" \
                 f"Description: {self.description}\n" \
                 f"Periodicity: {self.periodicity}\n" \
                 f"Created: {self.created}\n" \
                 f"Description update: {self.descr_update}\n" \
                 f"Active: {self.active}\n"
        return result
    

@serialize
@dataclass(frozen=True, order=True)
class CheckOff:
    '''
        Represents a habit check-off record.
        Initialized with 
        : param habit_title: str title of the habit,
        : param emotion: int emotion at the time of check-off from 0(neutral) to 5(very positive)
        : param created: date when the record is made
    
        new_check_off = CheckOff("Morning run", 3, today)
    '''
    habit_title: str
    emotion: int
    created: date
    
    def _save_element(self, file_name: str) -> None:
        ''' This method is saving one new element to the end of JSON file without 
            loading the whole collection from the file to memory, as there will be a long 
            history of check-offs at some point this will save time and memory.
        '''
        to_save = json.dumps(self.serialize())   # type: ignore[attr-defined]
        try:
            with open(file_name, "r+", encoding="UTF-8") as file:    
                file.seek(0,2)                   # set the file pointer to end of the file
                if file.tell() > 0:              # if the file is not empty do:
                    position = file.tell() - 1   # position is one char before the end = "]"                 
                    file.seek(position)
                    file.write(f",{to_save}]")   # replace "]" with ",{data}]"
                else: file.write(f"[{to_save}]")
        except FileNotFoundError:                #if file does not exist - create it and write new element
            with open(file_name, "w", encoding="UTF-8") as file:
                file.write(f"[{to_save}]")
                

class ObjectManager:
    ''' Parent class for HabitManager and CheckOffManager classes (below). Contains shared methods
        for loading data from and to the JSON file.
    
        Initialized with 
        : param file_name: str name fo the JSON to store the data, separete files for Habit's and CheckOff's
        : param today: date is a today date for creating and modifying Habit and CheckOff objects
        : param object_list: list[Any] is a list of Habit's or CheckOff's to be used by methods
    
        Note: this class is never used directly, only as parent for HabitManager and CheckOffManager.
    '''
    def __init__(self, file_name: str, today: date) -> None:
        self.file_name: str = file_name
        self.today: date = today
        self.object_list: list[Any] = []
    
    def _load_generator(self) -> Iterable[dict[str, str]]:
        ''' Generator loading records from JSON file one by one. Saves memory if sequence in the file
            is big. Probably this is not an issue for this application, but it probably is for ML-projects,
            so I chose to try it.
        '''
        try:
            if os.stat(self.file_name).st_size != 0:                  # if file is not empty
                with open(self.file_name, encoding="UTF-8") as file:
                    yield from json.load(file) 
        except FileNotFoundError:
            pass
    
    def _deserialize(self, klass: type[Any]) -> Iterable[Any]:
        ''' Generator of Habit or CheckOff objects received from JSON file. 
            We have only 4 types in our records: int, bool, str and date. 
            Date is serialized as str, so we need to deserialize it back to date.
        '''
        result = {}
        date_pattern = r"\d\d\d\d-\d\d-\d\d"                                 #date text pattern
        if self._load_generator():
            for element in self._load_generator():
                value: Union[str, date]
                for key, value in element.items():
                    if isinstance(value, str) and match(date_pattern, value):
                        value = datetime.strptime(value, '%Y-%m-%d').date()  
                    result[key] = value                       
                yield klass(**result)                                   
            
    def _save_list(self, source: Iterable[Any]) -> None:
        ''' Streaming objects to JSON file from source: list or generator.
            Simplejson mudule used as json to serialize Iterable object.
        '''
        to_save = json.dumps((obj.serialize() for obj in source), iterable_as_array=True) 
        with open(self.file_name, "w", encoding="UTF-8") as file:
            file.write(to_save)
     

class HabitManager(ObjectManager):
    ''' This is the main working class for Habits. Usually we start with building a list or generator
        of the Habit objects for further processing, like printing, adding, modifying and deleting.
    '''
    def make_list(self) -> None:
        self.object_list = [elem for elem in self._deserialize(Habit) 
                            if elem.active == True]             
    
    def make_gen(self, archived: bool=False) -> Iterable[Habit]:
        yield from (elem for elem in self._deserialize(Habit)   
                    if elem.active != archived)                 
            
    def _print_habits(self) -> Iterable[tuple[int, Habit]]:
        ''' Printing is done by loading sequence from generator, enumerating it and making two 
            sequence copies. One will be used for printing, another returned. For nice prining 
            we use "tabulate" module, which prints from a data in the list. So we convert Habit
            objects to the list of params.
        '''
        habit_gen = self.make_gen()
        result: list[Any] = [['N','Habit','Description','Periodicity','Created','Last update']]
        collection = enumerate(habit_gen, start=1)
        coll1, coll2 = itertools.tee(collection, 2)     
        # tabulating data to a list of lists
        for index, habit in coll1:
            habit_to_list = [str(values) for key, values in asdict(habit).items() if key != "active"]
            enum_habit = [index, *habit_to_list]
            result.append(enum_habit)                                        
        table = tabulate(result, headers='firstrow')
        print(table)
        return coll2
    
    def _check_duplicates(self, 
                         habit_title: Optional[str] = None,
                         habit_descr: Optional[str] = None
                        ) -> bool:
        ''' This method is checking if a new habit title or decription is already in the database.
            So it accepts title or description (that's why they are Optional) and searches for duplicates
            using generator.        
        '''
        if habit_title:
            for elem in self.make_gen():
                if elem.title == habit_title:
                    print("There is another habit with such title.")
                    return True
        if habit_descr:
            for elem in self.make_gen():
                if elem.description == habit_descr:
                    print("There is another habit with such description.")
                    return True    
        return False
    
    def add_habit(self, max_habit_title: int, max_habit_descr: int) -> bool:
        ''' This method add a new habit to the JSON habit file. It accepts the maximum length of
            habit title and habit description. By default it is 20 and 45 chars, so that table 
            of habits looks nice printed by tabulate.
        
            Process starts with printing all active habits and asking if the user is sure to add 
            a new habit. If yes, then they can type habit title, description and periodicity.
            
            If something goes wrong, like too long or short title, method reports problem and return 
            "True" to be used by the calling menu function to start over the menu in the while loop.
        '''
        print("List of registered habits:")
        self._print_habits()
        reply = input("Are you sure you want to add new habit? Type \"YES\" or anithing else if NO:")
        if reply != "YES": return True

        habit_title = input(f"Type min 1 and max {max_habit_title} "    # creating a habit title
                            f"chars title for a new habit:").capitalize()
        if len(habit_title) > max_habit_title or len(habit_title) < 1:
            print(f"Title is too short or too long. Try again.")
            return True
        
        # here we create a list (not generator) of habits because it is rather small and we are going 
        # to checked it two times in a row and then sort it before saving.
        self.make_list()
        if self._check_duplicates(habit_title=habit_title): return True
        
        #creating habit description
        habit_description = input(f"Type min 1 and max {max_habit_descr} "
                                  f"chars description for a new habit:").capitalize()
        if len(habit_description) > max_habit_descr or len(habit_description) < 1:
            print(f"Descriptionis too short or too long. Try again.")
            return True
        if self._check_duplicates(habit_descr=habit_description): return True
        
        #creating periodicity
        habit_per = input("Choose a new habit periodicity: type 1 for \"Daily\" and 2 for \"Weekly\"")
        if habit_per == '1': habit_per = "Daily"
        elif habit_per == '2': habit_per = "Weekly"
        else: 
            print("ValueError: Please choose 1 or 2")
            return True
        habit = Habit(habit_title, habit_description, habit_per, self.today, self.today)
        print(habit)             # printing ready new habit to check by user before saving  
        
        confirmation = input("Please, confirm by typing \"YES\" or abort by typing anything else:")
        if confirmation == "YES":
            print("Done! Updated list of habits is below:")
            self.object_list.append(habit)
            # sorting the list to look nice in the table when printed, list is always stored sorted
            self.object_list = sorted(self.object_list, key=lambda x: (x.periodicity,
                                                                       x.title)
                                      )
            self._save_list(self.object_list)
            self._print_habits()
        else: 
            print("Action aborted.")
        return True
            
    def delete_habit(self, check_off_manager: "CheckOffManager") -> bool:
        ''' This method deleting a habit and updates JSON file. 
        
            It accepts a check-off manager object to be able to delete corresponding check-offs
            together with their habit.
        
            Process starts with printing a list of active habits (there is no method for deleting
            archived habits in this version) and asking for a chosen habit.
            
            Then user has to confirm the delete process. They get warning that check-off history 
            will be lost also.
            
            Then check-off history is deleted by generating the sequence of all check-offs without
            those to be deleted. This sequence is then saved over the previous one. Very little 
            memory is used.
            
            For removing habit we use a list of habits, as this list is rather short. No sorting
            before saving is needed, because the list is already sorted.
        '''
        
        chosen_habit = self.choose_habit()     #habit to be deleted
        if not chosen_habit: return True
        
        reply = input(f"Warning! Habit and its check_off history will be lost."
                      f"Type YES to delete {chosen_habit.title}:")
        if reply != "YES": 
            print("Delete operation aborted.")
            return True
        
        # first we delete check_off history
        new_check_off_gen = (elem for elem in check_off_manager.make_gen()
                             if elem.habit_title != chosen_habit.title)
        check_off_manager._save_list(new_check_off_gen)
        
        # now update habit list
        self.make_list()
        self.object_list.remove(chosen_habit)
        self._save_list(self.object_list)
        print("Done! Updated list of habits:")
        self._print_habits()
        return True
    
    def _modify(self, 
               obj: Habit, 
               new_descr: Optional[str] = None,
               archive: Optional[bool] = None
               ) -> None:
        ''' This is private method modifying habit in description or archiving it.
            It accepts Habit object to deal with, new description or archiving command.
            As habits are frozen objects, we create a new habit object with new description
            or "active" attr, remove the old one and save the sorted list to the JSON file.
        '''
        habit_dict = asdict(obj)
        if new_descr: 
            habit_dict['description'] = new_descr
            habit_dict['descr_update'] = self.today
        if archive: habit_dict['active'] = False
        new_habit = Habit(**habit_dict)               
        self.object_list.append(new_habit)           
        self.object_list.remove(obj)
        self.object_list = sorted(self.object_list, key=lambda x:  (x.periodicity, 
                                                                    x.title)
                                 )    
        self._save_list(self.object_list)
        
    def modify_description(self) -> bool:
        ''' This is public habit description modification method, called by correspnding menu 
            fucntion. It lets the user choose a habit to be modified. Then creates a list of 
            habits, recives a new description, checks it for length and duplicates in the
            data base and if it's all good, uses _modify method. The new list of habits is
            printed to show the result of the update.
        '''
        chosen_habit = self.choose_habit()
        if not chosen_habit: return True
        self.make_list()
        new_description = input("Type min 1 and max 45 chars description for a new habit:").capitalize()
        if len(new_description) > 45 or len(new_description) < 1:
            print(f"Too long or too short description. Try again.")
            return True
        if self._check_duplicates(habit_descr=new_description): return True
        self._modify(chosen_habit, new_descr = new_description)
        print("Done! New list of habits:")
        self._print_habits()
        return True
    
    def archive_habit(self) -> bool:
        ''' This publis method is called my menu function to change "active" attr of a chosen
            habit. First user chooses the function to be archived. Then it creates a list of
            active habits, calls _modify method to replace the chosen habit with a new one.
            Printing the new list of active habits should prove the change is done. 
            
            Also the list of archived habits can be seen in Dashboard menu / Archived habits .
        '''
        chosen_habit = self.choose_habit()
        if not chosen_habit: return True
        self.make_list()
        self._modify(chosen_habit, archive=True)
        print("Done! New list of active habits:")
        self._print_habits()
        return True
        
    def choose_habit(self) -> Optional[Habit]:
        ''' This is public method for choosing a habit from the list of habits. It is public because
            also used by CheckOffManager methods. First it prints enumerated list of habits to be 
            chosen from and returns a chosen habit or None if habit list is empty.
        '''
        if enum_to_print := list(self._print_habits()):
            habit_num = int(input("Choose a habit:"))
            if len(enum_to_print) < habit_num or habit_num < 1:
                print(f"Input number is less than 1 or more than {len(enum_to_print)}. Try again.")
                return None
            chosen_habit = enum_to_print[habit_num - 1][1]
            print(f"You chose: {chosen_habit.title!r}")
            return chosen_habit
        else:
            print("There is no habits registred yet. Register your first habit.")
            return None
        

class CheckOffManager(ObjectManager):
    ''' This class contains specific methods for processing check-offs. It can make a list of check-offs
        with a given habit title and given number of recent elements to print. It also creates a 
        generator of all check-offs and special generator for streak function.
        
        Two main public methods: add new checkpoff and delete check-off. 
    '''
    def make_list(self, habit_name: str, print_number: Optional[int] = None) -> None:
        if print_number: 
            self.object_list = [elem for elem in self._deserialize(CheckOff) 
                                if elem.habit_title == habit_name][-print_number:]  #last N check-offs of the habit
        else:
            self.object_list = [elem for elem in self._deserialize(CheckOff) 
                                 if elem.habit_title == habit_name]

    
    def make_gen(self, habit_name: Optional[str] = None) -> Iterable[Any]:
        if not habit_name: yield from self._deserialize(CheckOff) 
        else: 
            self.make_list(habit_name)
            yield from zip(self.object_list, self.object_list[1:])  # this gen is for streak func
        
    def _print_check_offs(self, habit_name: str, print_number: int) -> Iterable[tuple[int, Any]]:
        ''' This private method prints the last (by the date) check-offs for a given habit title.
            This is done before adding a new check-off to briefly review recent check-off history 
            and improve motivation. For printing "tabulate" module is used.
            
            Method returns generator with enumerated list of check-offs.
        '''
        self.make_list(habit_name, print_number)
        result: list[Any] = [['N','Habit','Emotion','Created']]
        collection = enumerate(self.object_list, start=1)
        coll1, coll2 = itertools.tee(collection, 2)
        for index, check_off in coll1:
            check_off_to_list = [str(values) for key, values in asdict(check_off).items()]
            check_off_to_enum_list = [index, *check_off_to_list]     
            result.append(check_off_to_enum_list)
        table = tabulate(result, headers='firstrow')
        print(table)
        return coll2
   
    def report_check_off(self, chosen_habit: Habit, print_number: int) -> bool:
        ''' This is public method called by a check-off menu to report a new check-off. 
            First it prints out several (by default 5) last cehck-offs of a chosen habit.
            Then checks if this habit was already checked-off today (not allowed to check-off
            a habit twice in the same day).
            
            Then users inputs emotional level after the bait realization: from 0 to 5. And after
            checking this number CheckOff instance is created and saved. New list of
            recent check-offs is printed to show that the update is done.
            
            Method always return "True" to run again the menu function in a while loop.            
        '''
        print(f"Last {print_number} check_offs of the habit: {chosen_habit.title!r}")
        self._print_check_offs(chosen_habit.title, print_number)
        # test if habit was already checked-off today:
        if self.today - self.object_list[-1].created < timedelta(days=1):
            print("This habit was already checked-off today.")
            return True
        emotion = int(input("Choose emotion level after you have completed the habit from"
                            " 0(no emotions or negative) to 5(very positive)"))
        if emotion < 0 or emotion > 5: 
            print("ValueError: Choose number between 0 and 5")
            return True
        check_off_instance = CheckOff(chosen_habit.title, emotion, self.today)
        check_off_instance._save_element(self.file_name)
        print("Done!")
        self._print_check_offs(chosen_habit.title, print_number)
        return True
        
    def delete_check_off(self, chosen_habit: Habit, print_number: int) -> bool:
        ''' This public method is called by check-oof menu to delete some check-off inputed
            by mistake. It prints most (by default 5) recent check-offs for a given habit
            and user chooses which to delete. 
            
            Then method generates a sequence of check-offs without chosen one and saves it 
            back to JSON file. Generator is using minimum memory for this operation.
            
            Finally update list of most recent check-offs is printed to show the result.            
            Method always return "True" to run again the menu function in a while loop. 
        '''
        print(f"Last {print_number} check_offs of the habit: {chosen_habit.title!r}")
        collection = list(self._print_check_offs(chosen_habit.title, print_number))    
        reply = int(input("Choose check_off number to delete:"))
        if reply < 1 or reply > len(collection): 
            print(f"ValueError: Choose number between 1 and {len(collection)}.")
            return True
        #Generate the whole history of check-offs without deleted one
        new_check_off_gen = (elem for elem in self.make_gen() 
                                if elem != collection[reply - 1][1])
        self._save_list(new_check_off_gen)
        print("Done! Updated check_off list:")
        self._print_check_offs(chosen_habit.title, print_number)
        return True