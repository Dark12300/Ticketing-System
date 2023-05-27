"""User portal and login functions."""
import bcrypt
import getpass
import hashlib
import sqlite3
import time

from .display import (
    clear_screen,
    display_prices,
    display_ticket,
    dtype,
    input_validate,
)

class UserPortal():
    """Main class for user portal and login functions."""
    def __init__(self, main_database: sqlite3.Connection):
        """Initialisation for variables."""
        #command variables
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
        
        #login and user portal variables
        self.current_user = ""
        self.current_privilege = None   #1: admin, 0: standard

        self.power_off = False
        self.login_attempts = 0
        self.login_cooldown = 10 * 60   #seconds
        self.last_login_attempt = None   #UNIX time

        self.main_database = main_database
        self.entrance_prices = self.main_database.entrance_prices

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
        
        user_row = self.main_database.return_user_row(username)
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
                    display_prices(self.entrance_prices, slow_type = False)
                    print()

                elif "-u" in arguments or "--update" in arguments:
                    if self.current_user_privilege != 1:
                        print("Permission denied.")
                        print()
                        continue

                    display_prices(self.entrance_prices, slow_type=False)
                    print()
                    print("Enter the new tickets prices:")
                    print()
                    
                    new_adult_price = input_validate("New adult ticket price:", "float", round_value=True, slow_type=False)
                    new_child_price = input_validate("New child ticket price:", "float", round_value=True, slow_type=False)
                    new_senior_price = input_validate("New senior ticket price:", "float", round_value=True, slow_type=False)
                    new_wristband_price = input_validate("New wristband price:", "float", round_value=True, slow_type=False)

                    self.main_database.update_prices(new_adult_price, new_child_price, new_senior_price, new_wristband_price)

                    print()
                    print("Changes complete.")
                    print()

            elif main_command == "tickets":
                if "-l" in arguments or "--list" in arguments:
                    latest_row = self.main_database.return_tickets(1)
                    if not latest_row:   #tickets table empty
                        print("Ticket database empty.")
                        print()
                        continue

                    total_rows = latest_row[0][0]
                    entries = input_validate(f"How many database entries would you like to list [total {total_rows}]:", "integer", slow_type = False)

                    rows = self.main_database.return_tickets(entries)
                    
                    print()
                    for row in rows:
                        print(f"---------- Ticket {row[0]} ----------")
                        display_ticket(*row[1:], slow_type=False)
                        print()

            elif main_command == "clear":
                clear_screen()

            elif main_command == "passwd":
                password = getpass.getpass(prompt="Enter current password: ")

                user_row = self.main_database.return_user_row(self.current_user)
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

                self.main_database.update_password(user_id, new_user_password, new_user_salt)
                print("Password updated.")
                print()

            elif main_command == "users":
                if "-l" in arguments or "--list" in arguments:
                    users = self.main_database.return_users()
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

                    current_users = self.main_database.return_users()
                    if any([new_username == user[1] for user in current_users]):   #username already exists
                        print("Username already exists.")
                        print()
                        continue

                    new_salt = bcrypt.gensalt().decode("utf-8")
                    password_hash = hashlib.sha256(f"{new_password}{new_salt}".encode("utf-8")).hexdigest()

                    self.main_database.add_user(new_username, password_hash, new_salt, new_user_privileges)
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

                    current_users = self.main_database.return_users()
                    if not any([username == user[1] for user in current_users]) or not username:   #username doesn't exist
                        print("Username does not exist.")
                        print()
                        continue

                    user_row = self.main_database.return_user_row(username)
                    if user_row[4] == 1:
                        print("Unable to delete admin account.")
                        print()
                        continue

                    self.main_database.delete_user(user_row[0])
                    print("User deleted.")
                    print()

                elif "-u" in arguments or "--update" in arguments:
                    new_username = input("Enter the new username: ")
                    print()
                    current_users = self.main_database.return_users()

                    if not new_username:
                        print("Invalid new username.")
                        print()
                        continue

                    if any([new_username == user[1] for user in current_users]):   #username already exists
                        print("Username already exists.")
                        print()
                        continue

                    user_row = self.main_database.return_user_row(self.current_user)
                    self.main_database.update_username(user_row[0], new_username)
                    self.current_user = new_username

                    print("Username updated.")
                    print()