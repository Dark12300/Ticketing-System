"""All functions involving the database."""
import bcrypt
import hashlib
import sqlite3
import time

from .display import (
    dtype,
)

class MainDatabase():
    """Main class for database functions."""
    def __init__(self):
        """Initialisation for variables."""
        #constants
        self.DATABASE_NAME = "main_database.db"

        #user portal variables
        self.default_username = "admin123"
        self.default_password = "password123"
        self.default_privilege = 1   #1: admin, 0: standard

        #prices - prices are tracked by this file, and other files retrieves them after being updated
        self.entrance_prices = {
            "adult_ticket": 20, 
            "child_ticket": 12, 
            "senior_ticket": 11, 
            "wristband": 20,
            }

    def connect_database(self) -> None:
        """Connect to the main database and create default values if the database is new."""
        try:
            self.database_connection = sqlite3.connect(self.DATABASE_NAME)
            self.database_cursor = self.database_connection.cursor()

            self.database_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            if not len(self.database_cursor.fetchall()):   #if no tables exist
                self.database_cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, salt TEXT, privilege INTEGER);")
                self.database_cursor.execute("CREATE TABLE prices (item TEXT, price REAL);")
                self.database_cursor.execute("CREATE TABLE tickets (id INTEGER PRIMARY KEY, adult_tickets INTEGER"
                                               + ", child_tickets INTEGER, senior_tickets INTEGER, wristbands INTEGER"
                                               + ", surname TEXT, parking_pass_required INTEGER, total_cost INTEGER, date_ordered INTEGER);")

                salt = bcrypt.gensalt().decode("utf-8")
                password_hash = hashlib.sha256(f'{self.default_password}{salt}'.encode('utf-8')).hexdigest()
                self.database_cursor.execute("INSERT INTO users (username, password, salt, privilege) VALUES (?, ?, ?, ?);", 
                                             (self.default_username, password_hash, salt, self.default_privilege))
                self.database_cursor.executemany("INSERT INTO prices VALUES (?, ?);", 
                                                 [(item, price) for item, price in self.entrance_prices.items()])

                self.database_connection.commit()
            else:
                price_rows = self.database_cursor.execute("SELECT item, price FROM prices;").fetchall()
                for item, price in price_rows:
                    self.entrance_prices[item] = price

        except Exception as error:
            print("Database connection unsuccessful.")
            print(f"Error: {error}")
            time.sleep(1)
            dtype("Exiting...")
            time.sleep(0.5)
            exit()

    def add_ticket(self, values: dict) -> None:
        """Add a ticket to the database."""
        self.database_cursor.execute("INSERT INTO tickets (adult_tickets, child_tickets"
                                     + ", senior_tickets, wristbands, surname, parking_pass_required"
                                     + ", total_cost, date_ordered) VALUES (?, ?, ?, ?, ?, ?, ?, ?);", 
                                     (values['adult_tickets'], values['child_tickets'], values['senior_tickets'], 
                                      values['wristbands'], values['surname'], values['parking_pass_required'], 
                                      values['total_cost'], values['date_ordered']))
        
        self.database_connection.commit()

    def add_user(self, username: str, password: str, salt: str, privilege: int) -> None:
        """Add a new user into the database."""
        self.database_cursor.execute("INSERT INTO users (username, password, salt, privilege) VALUES (?, ?, ?, ?);",
                                     (username, password, salt, privilege))
        
        self.database_connection.commit()

    def update_prices(self, adult_price: float, child_price: float, senior_price: float, wristband_price: float) -> None:
        """Update the current prices in the database."""
        self.entrance_prices["adult_ticket"] = adult_price
        self.entrance_prices["child_ticket"] = child_price
        self.entrance_prices["senior_ticket"] = senior_price
        self.entrance_prices["wristband"] = wristband_price
        self.database_cursor.executemany("INSERT INTO prices VALUES (?, ?);", ([item, price] for item, price in self.entrance_prices.items()))

        self.database_connection.commit()

    def update_password(self, id: int, new_password: str, new_salt: str) -> None:
        """Update a user's password in the database."""
        self.database_cursor.execute("UPDATE users SET password = ?, salt = ? WHERE id = ?;", (new_password, new_salt, id))

        self.database_connection.commit()

    def update_username(self, id: int, username: str) -> None:
        """Update a username in the database."""
        self.database_cursor.execute("UPDATE users SET username = ? WHERE id = ?;", (username, id))

    def return_user_row(self, username: str) -> tuple:
        """Query and return a user's row from the database."""
        self.database_cursor.execute("SELECT * FROM users WHERE username = ?;", (username,))
        return self.database_cursor.fetchone()
    
    def return_users(self) -> list:
        """Query and return all users in the database."""
        self.database_cursor.execute("SELECT id, username FROM users;")
        return self.database_cursor.fetchall()
    
    def return_tickets(self, tickets: int) -> list:
        """Query and return x amount of most recent tickets in the database."""
        self.database_cursor.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT ?;", (tickets,))
        return self.database_cursor.fetchall()
    
    def delete_user(self, id: int) -> None:
        """Delete a user from the database."""
        self.database_cursor.execute("DELETE FROM users WHERE id = ?;", (id,))

        self.database_connection.commit()