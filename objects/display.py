"""Functions involving the display."""
import os
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

def display_prices(entrance_prices: dict, slow_type: bool = True) -> None:
    """Displays the current ticket prices."""
    if slow_type:
        print_method = dtype
    else:
        print_method = print
    
    left_align = 14
    right_align = 7

    print_method("Current prices for tickets are as follows:")
    for item, price in entrance_prices.items():
        price_formatted = f"£{price:.2f}"
        print_method(f"{item.replace('_', ' ').title():<{left_align}} : {price_formatted:>{right_align}}")

def display_ticket(*args, slow_type: bool = True) -> None:
        """Displays a ticket based on values from the arguments."""
        if slow_type:
            print_method = dtype
        else:
            print_method = print

        left_align = 14
        date_ordered = datetime.utcfromtimestamp(args[7]).strftime("%H:%M:%S GMT %d/%m/%Y") if isinstance(args[7], int) else args[7]
        print_method(f"{'Adult tickets':<{left_align}} : {args[0]}")
        print_method(f"{'Child tickets':<{left_align}} : {args[1]}")
        print_method(f"{'Senior tickets':<{left_align}} : {args[2]}")
        print_method(f"{'Wristbands':<{left_align}} : {args[3]}")
        print_method(f"{'Surname':<{left_align}} : {args[4]}")
        print_method(f"{'Parking pass':<{left_align}} : {'Yes' if args[5] else 'No'}")
        print_method(f"{'Total cost':<{left_align}} : £{args[6]:.2f}")
        print_method(f"{'Date ordered':<{left_align}} : {date_ordered}")