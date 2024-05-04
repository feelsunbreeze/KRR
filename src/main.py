import random
import json
from colorama import Fore, Style
import time
from backend import *

UNKNOWN_TRIGGER = Fore.RED + "I am not sure how to respond to that." + Style.RESET_ALL
BOT_NAME = "Mireska"
COLORS = [Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX]

def load_responses_from_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

responses = load_responses_from_json("responses.json")

def get_response(input_text, mode, tags=None):
    input_text = input_text.lower()
    if input_text == "mode prolog" and mode == "prolog":
        return Fore.LIGHTMAGENTA_EX + "You are already in Prolog mode." + Style.RESET_ALL
    if mode == "prolog":
        capitalized_text = ' '.join([word.capitalize() for word in input_text.split()])
        tags = pos_tag(capitalized_text.split())
        if tags[0][0].lower() == "who" or tags[0][0].lower() == "what":
            name = next((word for word, tag in tags if tag == 'NNP'), None)
            return to_natural_language(fetch_data_from_neo4j(name))

        if "define" in input_text:
            words = input_text.split()
            define_index = words.index("define")
            if define_index + 1 < len(words):
                word = words[define_index + 1]
                return (word.capitalize() + " is " + get_definition(word) + ".")
            else:
                return UNKNOWN_TRIGGER

    for response_category in responses.values():
        for word in response_category["triggers"]:
            pattern = re.escape(word)  # Escape special characters in the pattern
            pattern = f"\\b{pattern}\\b"  # Match whole words only
            if re.search(pattern, input_text):
                return random.choice(response_category["responses"])
    return fetch_data_from_neo4j(input_text)

def slow_print(text, delay=0.05):
    if isinstance(text, list):
        for i, item in enumerate(text):
            for char in item:
                print(char, end='', flush=True)
                time.sleep(delay)
            print('.', end=' ')
    else:
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)

def chat():
    mode = "chat"
    rainbow_name = ""
    for i, letter in enumerate(BOT_NAME):
        rainbow_name += COLORS[i % len(COLORS)] + letter
    slow_print(f"Welcome to {rainbow_name}", delay=0.01)
    print()
    while True:
        user_input = input(Fore.LIGHTCYAN_EX + "\nYou: " + Style.RESET_ALL)
        tagged_words = None
        if user_input == "mode prolog" and mode == "chat":
            mode = "prolog"
            while True:
                try:
                    file_name = str(input(Fore.LIGHTYELLOW_EX + "Enter the name of the Prolog file in current dir (i.e: prolog.pl) or you can skip adding a file by typing \"skip\": " + Style.RESET_ALL))
                    if file_name == "skip":
                        init_backend()
                        print(Fore.LIGHTMAGENTA_EX + "Skipping prolog file.." + Style.RESET_ALL)
                    else:
                        init_backend(file_name)
                        print(Fore.GREEN + "Data imported successfully!" + Style.RESET_ALL)
                    break
                except Exception as e:
                    print(Fore.RED + str(e) + Style.RESET_ALL)
            continue
        if mode == "prolog":
            if user_input.lower() == "mode chat":
                mode = "chat"
                slow_print(Fore.LIGHTMAGENTA_EX + "Switching to chat mode.." + Style.RESET_ALL + "\n")
                continue
            words = user_input.split()
            tagged_words = pos_tag(words)
        response = get_response(user_input, mode, tagged_words)
        slow_print(Fore.LIGHTGREEN_EX + f"{BOT_NAME}: " + Style.RESET_ALL, delay=0.03)
        slow_print(response, delay=0.05)
        print()
        if any(trigger in user_input.lower() for trigger in responses.get("farewell", {}).get("triggers", [])):
            break
        

if __name__ == "__main__":
    chat()