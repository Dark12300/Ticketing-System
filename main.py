"""Ticketing system program which allows customers to make orders, 
and an admin to customise the options.
***The program is made based on a school project.***
"""
import bcrypt
import getpass
import hashlib
import os
import sqlite3
import time
from datetime import datetime
from typing import Union

def dtype(text: str) -> None:
    """A function which prints each character in a message with a delayed typing effect."""
    for character in text:
        print(character, flush=True, end="")
        time.sleep(0.03)
    print()

def input_validate(text: str, data_type: str, round_value: bool = False, slow_type: bool = True) -> Union[int, bool, float]:
    """A generic function which iteratively error handles a user 
    input until the user provides a specific data type.
    """
    error_messages = {
        "integer": "Please enter a positive integer.", 
        "float": "Please enter an integer or decimal.", 
        "bool": "Please enter yes/y/no/n.",
        }
    
    if slow_type:
        print_method = dtype
    else:
        print_method = print

    print_method(text)
    value = input()
    while True:
        if data_type == "integer" and value.isnumeric():
            value = int(value)
            break
            
        elif data_type == "float" and value.replace(".", "").isnumeric():   #accepts integers
            value = round(float(value), 2) if round_value else float(value)
            break

        elif data_type == "bool" and value in ["yes", "y", "no", "n"]:
            value = True if value.lower() in ["yes", "y"] else False
            break

        print_method(error_messages[data_type])
        print_method(text)
        value = input()

    return value

def clear_screen() -> None:
    """A function to clear the screen."""
    os.system("cls" if os.name == "nt" else "clear")

class TicketingSystem():
    """Main class including methods for ticketing system."""
    def __init__(self) -> None:
        """Initialisation - creating variables and connecting to database."""
        #constants
        self.MAXIMUM_CAPACITY = 500
        self.DATABASE_NAME = "main_database.db"

        #tracking variables
        self.customers = 0
        self.entrance_prices = {
            "adult_ticket": 20, 
            "child_ticket": 12, 
            "senior_ticket": 11, 
            "wristband": 20,
            }

        #user portal variables
        self.current_user = ""
        self.current_user_privilege = None   #0: non-admin, 1: admin
        self.default_username = "admin123"
        self.default_password = "password123"
        self.default_user_privilege = 1

        self.power_off = False
        self.login_attempts = 0
        self.login_cooldown = 10 * 60   #seconds
        self.last_login_attempt = None   #UNIX time
        self.commands = {
            "shutdown": [], 
            "exit": [], 
            "help": [], 
            "prices": ["-l", "--list", "-u", "--update"], 
            "tickets": ["-l", "--list"],
            "clear": [],
            "passwd": [],
            "users": ["-l", "--list", "-a", "--add", "-d", "--delete", "-u", "--update"]
            }   #command, args
        self.command_help = {
            "shutdown": ["Shutdown the system."], 
            "exit": ["Exit the user portal."], 
            "help": ["Show command information."],

            "prices": [
                "-l, --list  List the current prices.",
                "-u, --update  Update the current prices.",
                ],

            "tickets": [
                "-l, --list  List [x] most recent ticket records.",
                ], 
            "clear": ["Clears the screen."],
            "passwd": ["Change the password for the current user."],
            "users": [
                "-l, --list  List the users registered on the system.",
                "-a, --add  Add a user to the system.",
                "-d, --delete  Delete a user from the system.",
                "-u, --update  Update the current user's username.",
                ]
            }

        dtype("Launching program...")
        time.sleep(1)

        dtype("Connecting to database...")
        self.connect_database()
        time.sleep(1)
        dtype("Connection successful.")
        print()
        time.sleep(1)

        dtype("Clearing screen and entering main program...")
        time.sleep(1)
        clear_screen()
        
        self.ticket_program()

    def update_prices_from_database(self) -> None:
        """Updates the prices dictionary from the values in the database."""
        price_rows = self.database_cursor.execute("SELECT item, price FROM prices;").fetchall()
        for item, price in price_rows:
            self.entrance_prices[item] = price

    def connect_database(self) -> None:
        """Connect to the main database and create default values if the database is new."""
        try:
            self.database_connection = sqlite3.connect(self.DATABASE_NAME)
            self.database_cursor = self.database_connection.cursor()

            self.database_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            if not len(self.database_cursor.fetchall()):   #if not tables exist
                self.database_cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, salt TEXT, admin_privileges INTEGER);")
                self.database_cursor.execute("CREATE TABLE prices (item TEXT, price REAL);")
                self.database_cursor.execute("CREATE TABLE tickets (id INTEGER PRIMARY KEY, adult_tickets INTEGER"
                                               + ", child_tickets INTEGER, senior_tickets INTEGER, wristbands INTEGER"
                                               + ", surname TEXT, parking_pass_required INTEGER, total_cost INTEGER, date_ordered INTEGER);")

                salt = bcrypt.gensalt().decode("utf-8")
                password_hash = hashlib.sha256(f'{self.default_password}{salt}'.encode('utf-8')).hexdigest()
                self.database_cursor.execute("INSERT INTO users (username, password, salt, admin_privileges) VALUES (?, ?, ?, ?);", 
                                             (self.default_username, password_hash, salt, self.default_user_privilege))
                self.database_cursor.executemany("INSERT INTO prices VALUES (?, ?);", 
                                                 [(item, price) for item, price in self.entrance_prices.items()])

                self.database_connection.commit()
            else:
                self.update_prices_from_database()

        except Exception as error:
            print("Database connection unsuccessful.")
            print(f"Error: {error}")
            time.sleep(1)
            dtype("Exiting...")
            time.sleep(0.5)
            exit()

    def display_prices(self, slow_type: bool = True) -> None:
        """Displays the current ticket prices."""
        if slow_type:
            print_method = dtype
        else:
            print_method = print
        
        left_align = 14
        right_align = 7

        print_method("Current prices for tickets are as follows:")
        for item, price in self.entrance_prices.items():
            price_formatted = f"£{price:.2f}"
            print_method(f"{item.replace('_', ' ').title():<{left_align}} : {price_formatted:>{right_align}}")
    
    def display_ticket(self, *args, slow_type: bool = True) -> None:
        """Displays a ticket based on values from the arguments."""
        if slow_type:
            print_method = dtype
        else:
            print_method = print

        left_align = 14
        date_ordered = datetime.utcfromtimestamp(args[7]).strftime("%H:%M:%S GMT %d/%m/%Y") if args[7] != "NA" else "NA"
        print_method(f"{'Adult tickets':<{left_align}} : {args[0]}")
        print_method(f"{'Child tickets':<{left_align}} : {args[1]}")
        print_method(f"{'Senior tickets':<{left_align}} : {args[2]}")
        print_method(f"{'Wristbands':<{left_align}} : {args[3]}")
        print_method(f"{'Surname':<{left_align}} : {args[4]}")
        print_method(f"{'Parking pass':<{left_align}} : {'Yes' if args[5] else 'No'}")
        print_method(f"{'Total cost':<{left_align}} : £{args[6]:.2f}")
        print_method(f"{'Date ordered':<{left_align}} : {date_ordered}")

    def add_ticket_to_database(self) -> None:
        """Updates the database with any new tickets ordered."""
        self.database_cursor.execute("INSERT INTO tickets (adult_tickets, child_tickets"
                                     + ", senior_tickets, wristbands, surname, parking_pass_required"
                                     + ", total_cost, date_ordered) VALUES (?, ?, ?, ?, ?, ?, ?, ?);", 
                                     (self.adult_tickets, self.child_tickets, self.senior_tickets, 
                                      self.wristbands, self.surname, self.parking_pass_required, 
                                      self.total_cost, self.date_ordered_unix))
        self.database_connection.commit()

    def return_user_row(self, username: str) -> tuple:
        """Return the user row from the database."""
        self.database_cursor.execute("SELECT * FROM users WHERE username = ?;", (username,))
        return self.database_cursor.fetchone()
    
    def return_users(self) -> list:
        """Return all users registered on the system."""
        self.database_cursor.execute("SELECT id, username FROM users;")
        return self.database_cursor.fetchall()

    def login(self) -> bool:
        """Verify a user with a username and password."""
        if self.login_attempts >= 5:
            cooldown = True if (time.time() - self.last_login_attempt) > self.login_cooldown else False
            if not cooldown:
                time_left = self.login_cooldown - (time.time() - self.last_login_attempt)
                dtype("Too many failed login attempts.")
                dtype(f"Cooldown time left: {round(time_left / 60, 1)} minute/s.")
                print()
                time.sleep(1.5)
                return False
            
            self.login_attempts = 0
        
        username = input("Enter username: ")
        password = getpass.getpass(prompt="Enter password: ")
        
        user_row = self.return_user_row(username)
        if not user_row:   #user doesn't exist
            self.login_attempts += 1
            self.last_login_attempt = time.time()
            print("Username or password incorrect.")
            print()
            time.sleep(1)
            return False
        
        user_password = user_row[2]
        user_salt = user_row[3]

        password_hash = hashlib.sha256(f"{password}{user_salt}".encode("utf-8")).hexdigest()
        if user_password != password_hash:
            self.login_attempts += 1
            self.last_login_attempt = time.time()
            print("Username or password incorrect.")
            print()
            time.sleep(1)
            return False
        
        self.login_attempts = 0
        self.current_user = username
        self.current_user_privilege = user_row[4]
        return True
    
    def user_portal(self) -> None:
        """A shell for a user to execute commands. The admin user will have escalated privileges."""
        print()
        dtype("Welcome to the user portal!")
        print()

        exit_loop = False
        while not exit_loop:
            user_command = input(f"{self.current_user}>").strip()
            main_command, *arguments = user_command.split(" ")
            
            if main_command == "":
                continue

            if main_command not in self.commands.keys():
                print("For command information, type help.")
                print()
                continue

            if any([argument not in self.commands[main_command] for argument in arguments]):
                print("For command information, type help.")
                print()
                continue

            if main_command == "shutdown":
                self.power_off = True
                exit_loop = True

            elif main_command == "exit":
                exit_loop = True
                clear_screen()

            elif main_command == "help":
                for command, information_list in self.command_help.items():
                    print(f"{command} -")
                    for information in information_list:
                        print(f"{information}")
                    print()

            elif main_command == "prices":
                if "-l" in arguments or "--list" in arguments:
                    self.display_prices(slow_type = False)
                    print()

                elif "-u" in arguments or "--update" in arguments:
                    if self.current_user_privilege != 1:
                        print("Permission denied.")
                        print()
                        continue

                    self.display_prices(slow_type=False)
                    print()
                    print("Enter the new tickets prices:")
                    print()
                    
                    new_adult_price = input_validate("New adult ticket price:", "float", round_value=True, slow_type=False)
                    new_child_price = input_validate("New child ticket price:", "float", round_value=True, slow_type=False)
                    new_senior_price = input_validate("New senior ticket price:", "float", round_value=True, slow_type=False)
                    new_wristband_price = input_validate("New wristband price:", "float", round_value=True, slow_type=False)
                    print()
                    print("Changes complete.")
                    print()

                    self.entrance_prices["adult_ticket"] = new_adult_price
                    self.entrance_prices["child_ticket"] = new_child_price
                    self.entrance_prices["senior_ticket"] = new_senior_price
                    self.entrance_prices["wristband"] = new_wristband_price

                    self.database_cursor.executemany("INSERT INTO prices VALUES (?, ?);", 
                                                     [(item, price) for item, price in self.entrance_prices.items()])
                    self.database_connection.commit()

            elif main_command == "tickets":
                if "-l" in arguments or "--list" in arguments:
                    self.database_cursor.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT 1;")
                    total_rows = self.database_cursor.fetchone()
                    if not total_rows:   #database empty
                        print("Ticket database empty.")
                        print()
                        continue

                    total_rows = total_rows[0]
                    entries = input_validate(f"How many database entries would you like to list [total {total_rows}]:", "integer", slow_type = False)

                    self.database_cursor.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT ?;", (entries,))
                    rows = self.database_cursor.fetchall()

                    print()
                    for row in rows:
                        print(f"---------- Ticket {row[0]} ----------")
                        self.display_ticket(*row[1:], slow_type=False)
                        print()

            elif main_command == "clear":
                clear_screen()

            elif main_command == "passwd":
                password = getpass.getpass(prompt="Enter current password: ")

                user_row = self.return_user_row(self.current_user)
                user_id = user_row[0]

                user_password = user_row[2]
                user_salt = user_row[3]
                password_hash = hashlib.sha256(f"{password}{user_salt}".encode("utf-8")).hexdigest()
                if user_password != password_hash:
                    print("Password incorrect.")
                    print()
                    continue

                new_password = getpass.getpass(prompt="Enter new password: ")
                new_user_salt = bcrypt.gensalt().decode("utf-8")
                new_user_password = hashlib.sha256(f"{new_password}{new_user_salt}".encode("utf-8")).hexdigest()

                self.database_cursor.execute("UPDATE users SET password = ?, salt = ? WHERE id = ?", (new_user_password, new_user_salt, user_id))
                self.database_connection.commit()
                print("Password updated.")
                print()

            elif main_command == "users":
                if "-l" in arguments or "--list" in arguments:
                    users = self.return_users()
                    for user in users:
                        print(f"{user[0]}: {user[1]}")
                    print()

                elif "-a" in arguments or "--add" in arguments:
                    if self.current_user_privilege != 1:
                        print("Permission denied.")
                        print()
                        continue

                    new_username = input("Enter the new username: ")
                    new_password = getpass.getpass(prompt="Enter the new password: ")
                    new_user_privileges = input_validate("Is the new user an admin?", "bool", slow_type=False)
                    print()
                    if not new_username or not new_password:   #empty username or password
                        print("Invalid new username or password.")
                        print()
                        continue

                    current_users = self.return_users()
                    if any([new_username == user[1] for user in current_users]):   #username already exists
                        print("Username already exists.")
                        print()
                        continue

                    new_salt = bcrypt.gensalt().decode("utf-8")
                    password_hash = hashlib.sha256(f"{new_password}{new_salt}".encode("utf-8")).hexdigest()

                    self.database_cursor.execute("INSERT INTO users (username, password, salt, admin_privileges) VALUES (?, ?, ?, ?);", 
                                                 (new_username, password_hash, new_salt, new_user_privileges))
                    self.database_connection.commit()
                    print("User added.")
                    print()

                elif "-d" in arguments or "--delete" in arguments:
                    if self.current_user_privilege != 1:
                        print("Permission denied.")
                        print()
                        continue

                    username = input("Enter the username: ")
                    print()
                    if username == self.current_user:
                        print("Unable to delete current user.")
                        print()
                        continue

                    current_users = self.return_users()
                    if not any([username == user[1] for user in current_users]) or not username:   #username doesn't exist
                        print("Username does not exist.")
                        print()
                        continue

                    user_row = self.return_user_row(username)
                    if user_row[4] == 1:
                        print("Unable to delete admin account.")
                        print()
                        continue

                    self.database_cursor.execute("DELETE FROM users WHERE id = ?;", (user_row[0],))
                    self.database_connection.commit()

                    print("User deleted.")
                    print()

                elif "-u" in arguments or "--update" in arguments:
                    new_username = input("Enter the new username: ")
                    print()
                    current_users = self.return_users()

                    if not new_username:
                        print("Invalid new username.")
                        print()
                        continue

                    if any([new_username == user[1] for user in current_users]):   #username already exists
                        print("Username already exists.")
                        print()
                        continue

                    user_row = self.return_user_row(self.current_user)
                    self.database_cursor.execute("UPDATE users SET username = ? WHERE id = ?;", (new_username, user_row[0]))
                    self.database_connection.commit()

                    self.current_user = new_username

                    print("Username updated.")
                    print()

    def ticket_program(self):
        """The main ticket program where customers can buy tickets."""
        while not self.power_off:
            #variables per customer
            self.adult_tickets = 0
            self.child_tickets = 0
            self.senior_tickets = 0
            self.wristbands = 0
            self.surname = ""
            self.parking_pass_required = None
            self.total_cost = 0
            self.date_ordered_unix = 0   #UNIX time

            dtype("Press enter to continue to the booking system.")
            enter_system = input()
            if enter_system == "login":
                if self.login():
                    self.user_portal()
                
                continue

            if self.customers >= self.MAXIMUM_CAPACITY:
                dtype("Unfortunately, the theme park is at maximum capacity and we will be unable to let you enter.")
                print()
                time.sleep(0.5)
                continue

            dtype("Welcome to the Copington Adventure Theme Park ticketing system.")
            time.sleep(0.5)

            print()
            self.display_prices()
            print()

            self.adult_tickets = input_validate("How many adult tickets would you like?", "integer")
            self.child_tickets = input_validate("How many child tickets would you like?", "integer")
            self.senior_tickets = input_validate("How many senior tickets would you like?", "integer")
            self.wristbands = input_validate("How many wristbands would you like for the rides?", "integer")
            self.total_cost = (self.adult_tickets * self.entrance_prices["adult_ticket"] 
                               + self.child_tickets * self.entrance_prices["child_ticket"] 
                               + self.senior_tickets * self.entrance_prices["senior_ticket"] 
                               + self.wristbands * self.entrance_prices["wristband"])
            time.sleep(0.5)

            dtype("What is the surname of the lead booker?")
            self.surname = input()
            time.sleep(0.5)

            self.parking_pass_required = input_validate("Do you require a parking pass?", "bool")
            time.sleep(0.5)

            clear_screen()
            dtype("To confirm, here is your current booking status:")
            self.display_ticket(self.adult_tickets, self.child_tickets, 
                                self.senior_tickets, self.wristbands, 
                                self.surname, self.parking_pass_required, self.total_cost, "NA")
            print()
            dtype("If your booking order is incorrect, please enter restart, else press enter to proceed.")
            time.sleep(0.5)
            confirmed = input().lower()
            if confirmed == "restart":
                dtype("Exiting current booking order...")
                print()
                time.sleep(0.5)
                clear_screen()
                continue

            clear_screen()
            dtype("Proceeding to payment details.")
            print()
            dtype(f"The total cost for your trip is £{self.total_cost:.2f}.")
            print()

            dtype("Please enter your payment in £10s and £20s:")
            total_payment_entered = 0
            while True:
                tens = input_validate("How many £10s would you like to pay:", "integer")
                twenties = input_validate("How many £20s would you like to pay:", "integer")
                total_payment_entered += + tens * 10 + twenties * 20
                if self.total_cost - total_payment_entered <= 0:   #payment complete
                    break

                dtype(f"You still need to pay £{self.total_cost - total_payment_entered:.2f}.")

            change = total_payment_entered % self.total_cost
            print()
            dtype("Payment accepted.")
            dtype(f"You have £{change:.2f} change.")
            time.sleep(1)
            clear_screen()

            dtype("Here is your ticket:")
            print()

            self.date_ordered_unix = int(time.time())
            self.display_ticket(self.adult_tickets, self.child_tickets, 
                                self.senior_tickets, self.wristbands, 
                                self.surname, self.parking_pass_required, 
                                self.total_cost, self.date_ordered_unix)
            time.sleep(0.5)

            print()
            dtype("Thank you for booking at Copington Adventure Theme Park!")
            print()

            self.customers += self.adult_tickets + self.child_tickets + self.senior_tickets   #update customer count
            self.add_ticket_to_database()   #update database with new ticket
            time.sleep(3)

            clear_screen()

        self.database_connection.close()

if __name__ == "__main__":
    ticketing_system = TicketingSystem()
    dtype("Shutting down...")
    time.sleep(1)
    exit()