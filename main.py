"""Ticketing system program which allows customers to make orders, 
and an admin to customise the options.
***The program is made based on a school project.***
"""
import time

from objects import *

class TicketingSystem():
    """Main class including methods for ticketing system."""
    def __init__(self) -> None:
        """Initialisation - creating variables and connecting to database."""
        #constants
        self.MAXIMUM_CAPACITY = 500

        #tracking variables
        self.customers = 0
        self.current_order = {}
        
        self.main_database = MainDatabase()
        self.portal_object = UserPortal(self.main_database)

        dtype("Launching program...")
        time.sleep(1)

        dtype("Connecting to database...")
        self.main_database.connect_database()
        self.entrance_prices = self.main_database.entrance_prices
        time.sleep(1)
        dtype("Connection successful.")
        print()
        time.sleep(1)

        dtype("Clearing screen and entering main program...")
        time.sleep(1)
        clear_screen()
        
        self.ticket_program()

    def ticket_program(self):
        """The main ticket program where customers can buy tickets."""
        while not self.portal_object.power_off:
            self.current_order = {"date_ordered": "N/A"}

            dtype("Press enter to continue to the booking system.")
            enter_system = input()
            if enter_system == "login":
                if self.portal_object.login():
                    self.portal_object.user_portal()
                
                continue

            if self.customers >= self.MAXIMUM_CAPACITY:
                dtype("Unfortunately, the theme park is at maximum capacity and we will be unable to let you enter.")
                print()
                time.sleep(0.5)
                continue

            dtype("Welcome to the Copington Adventure Theme Park ticketing system.")
            time.sleep(0.5)

            print()
            display_prices(self.entrance_prices)
            print()

            adult_tickets = input_validate("How many adult tickets would you like?", "integer")
            child_tickets = input_validate("How many child tickets would you like?", "integer")
            senior_tickets = input_validate("How many senior tickets would you like?", "integer")
            wristbands = input_validate("How many wristbands would you like for the rides?", "integer")
            total_cost = (adult_tickets * self.entrance_prices["adult_ticket"] 
                          + child_tickets * self.entrance_prices["child_ticket"] 
                          + senior_tickets * self.entrance_prices["senior_ticket"] 
                          + wristbands * self.entrance_prices["wristband"])
            
            self.current_order["adult_tickets"] = adult_tickets
            self.current_order["child_tickets"] = child_tickets
            self.current_order["senior_tickets"] = senior_tickets
            self.current_order["wristbands"] = wristbands
            self.current_order["total_cost"] = total_cost

            time.sleep(0.5)

            dtype("What is the surname of the lead booker?")
            surname = input()
            self.current_order["surname"] = surname
            time.sleep(0.5)

            parking_pass_required = input_validate("Do you require a parking pass?", "bool")
            self.current_order["parking_pass_required"] = parking_pass_required
            time.sleep(0.5)

            clear_screen()
            dtype("To confirm, here is your current booking status:")
            display_ticket(self.current_order)
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
            dtype(f"The total cost for your trip is £{total_cost:.2f}.")
            print()

            dtype("Please enter your payment in £10s and £20s:")
            total_payment_entered = 0
            while True:
                tens = input_validate("How many £10s would you like to pay:", "integer")
                twenties = input_validate("How many £20s would you like to pay:", "integer")
                total_payment_entered += tens * 10 + twenties * 20
                if total_cost - total_payment_entered <= 0:   #payment complete
                    break

                dtype(f"You still need to pay £{total_cost - total_payment_entered:.2f}.")

            change = total_payment_entered - total_cost
            print()
            dtype("Payment accepted.")
            dtype(f"You have £{change:.2f} change.")
            time.sleep(1)
            clear_screen()

            dtype("Here is your ticket:")
            print()

            self.current_order["date_ordered"] = int(time.time())
            display_ticket(self.current_order)
            time.sleep(0.5)

            self.customers += (adult_tickets
                               + child_tickets
                               + senior_tickets)   #update customer count
            self.main_database.add_ticket(self.current_order)   #update database with new ticket

            print()
            dtype("Thank you for booking at Copington Adventure Theme Park!")
            print()
            time.sleep(3)

            clear_screen()

        dtype("Closing database...")
        self.main_database.database_connection.close()
        time.sleep(1)

if __name__ == "__main__":
    ticketing_system = TicketingSystem()
    dtype("Shutting down...")
    time.sleep(1)
    exit()
