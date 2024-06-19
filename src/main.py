import random
import json
import time
from backend import *

HOST = get_ip()
PORT = 1234
UNKNOWN_TRIGGER = "I am not sure how to respond to that."  
BOT_NAME = "MuseBOT"
COLORS = [Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX]

def load_responses_from_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

responses = load_responses_from_json("responses.json")

def get_response(input_text, mode, tags=None):
    input_text = input_text.lower()
    
    if mode == "prolog":
        if input_text == "mode prolog":
            return Fore.LIGHTMAGENTA_EX + "You are already in Prolog mode." + Style.RESET_ALL
        
        # Capitalize each word in input text for proper tagging
        capitalized_text = ' '.join([word.capitalize() for word in input_text.split()])
        tags = pos_tag(capitalized_text.split())
        # Handle "who" or "what" queries
        if tags[0][0].lower() in ["who", "what"]:
            name = next((word for word, tag in tags if tag == 'NNP'), None)

            if "have" in input_text or "has" in input_text:
                create_conversation_node(input_text)
                return fetch_relationship_data_from_neo4j("has", name)
            
            if sum(1 for _, tag in tags if tag == 'NNP') > 1:
                result = []
                for word, tag in tags:
                    if tag == 'NNP':
                        result.extend(fetch_all_data_from_neo4j(word))
                result = [item for item in result if item != []]
                output = to_natural_language(result)
                output_with_nnp = [sentence for sentence in output if name.lower() in sentence.lower()]
                create_conversation_node(input_text)
                create_episodic_memory(input_text, capitalize_last_word(output_with_nnp))
                return capitalize_last_word(output_with_nnp)
            
            if name:
                data = fetch_all_data_from_neo4j(name)
                if data:
                    create_conversation_node(input_text)
                    create_episodic_memory(input_text, to_natural_language(data))
                    return to_natural_language(data)
        
        # Handle Song Requests
        if "play" in input_text and "by" in input_text:
            input_text = input_text.split("play")[1].strip()
            split_text = input_text.split("by")
            song_name = split_text[0].strip()
            artist_name = split_text[1].split()[0].strip(".,!?")
            get_song_location(song_name, artist_name)
            create_episodic_memory(input_text, f"Playing {song_name} by {artist_name}...")
            return f'Playing {song_name} by {artist_name}...'

        # Handle User Information Queries
        subject = None
        verb = None
        obj = None

        for word, tag in tags:
            if subject is None and (tag == 'NNP' or tag == 'NN' or tag == 'NNS'):
                subject = word.capitalize()
            elif subject is None and word == "I":
                subject = "User"
            elif verb is None and tag.startswith('NNP') or tag.startswith('VB') or tag.startswith('VBZ'):
                verb = word.lower()
            elif subject and verb and (tag == 'NN' or tag == 'NNP' or tag == 'JJ' or tag == 'NNS'):
                obj = word.capitalize()
                break
    
        if subject and verb and obj:
            process_sentence_for_neo4j(subject, verb, obj)
            create_conversation_node(input_text)
            create_episodic_memory(input_text, f"{subject} {verb} {obj} will be remembered.")
            return f"Alright, I will remember that!"
        
        # Handle "define" queries
        if "define" in input_text:
            words = input_text.split()
            define_index = words.index("define")
            if define_index + 1 < len(words):
                word = words[define_index + 1]
                create_conversation_node(input_text)
                definition = get_definition(word)
                create_episodic_memory(input_text, f"{word.capitalize()} is {definition}." if definition else f"No definition found for {word}.")
                return f"{word.capitalize()} is {definition}." if definition else f"No definition found for {word}."
            else:
                create_conversation_node(input_text)
                create_episodic_memory(input_text, UNKNOWN_TRIGGER)
                return UNKNOWN_TRIGGER
    
    # Default response using pre-defined triggers and responses
    for response_category in responses.values():
        for trigger in response_category["triggers"]:
            pattern = f"\\b{re.escape(trigger)}\\b"  # Match whole words only
            if re.search(pattern, input_text):
                create_conversation_node(input_text)
                choice = random.choice(response_category["responses"])
                create_episodic_memory(input_text, choice)
                return choice

    # If no known trigger matches, log the conversation and return default unknown trigger response
    create_conversation_node(input_text)
    create_episodic_memory(input_text, UNKNOWN_TRIGGER)
    return UNKNOWN_TRIGGER


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

def send_response(client_socket, response):
    if isinstance(response, list):
        # Encode each element in the list
        encoded_response = [(str(element) + ". ").encode() for element in response]
        # Send each encoded element
        for encoded_element in encoded_response:
            client_socket.sendall(encoded_element)
    else:
        # Directly encode and send the response if it's not a list
        client_socket.sendall(response.encode())


def chat(app=None):
    mode = "chat"
    if app is not None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((HOST, PORT))
            server_socket.listen(1)

            print(Fore.GREEN + f"Server listening on {HOST}:{PORT}" + Style.RESET_ALL)

            while True:
                client_socket, _ = server_socket.accept()

                with client_socket:
                    data = client_socket.recv(1024).decode()
                    print(Fore.LIGHTCYAN_EX + "\nYou: " + Style.RESET_ALL + data)
                    user_input = data.strip()

                    tagged_words = None
                    if user_input == "mode prolog" and mode == "chat":
                        mode = "prolog"
                        while True:
                            try:
                                file_name = str(input(Fore.LIGHTYELLOW_EX + "Enter the name of the Prolog file in current dir (i.e: prolog.pl) or you can skip adding a file by typing \"skip\": " + Style.RESET_ALL))
                                if file_name == "":
                                    raise Exception("Please enter a valid file name.")
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
                    send_response(client_socket, response)
                    slow_print(Fore.LIGHTGREEN_EX + f"{BOT_NAME}: " + Style.RESET_ALL, delay=0.03)
                    slow_print(response, delay=0.05)
                    print()


                    if any(trigger in user_input.lower() for trigger in responses.get("farewell", {}).get("triggers", [])):
                        break
    else:
        while True:
            user_input = input(Fore.LIGHTCYAN_EX + "\nYou: " + Style.RESET_ALL)
            tagged_words = None
            if user_input == "mode prolog" and mode == "chat":
                mode = "prolog"
                while True:
                    try:
                        file_name = str(input(Fore.LIGHTYELLOW_EX + "Enter the name of the Prolog file in current dir (i.e: prolog.pl) or you can skip adding a file by typing \"skip\": " + Style.RESET_ALL))
                        if file_name == "":
                            raise Exception("Please enter a valid file name.")
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
    start_neo4j()
    rainbow_name = ""
    for i, letter in enumerate(BOT_NAME):
        rainbow_name += COLORS[i % len(COLORS)] + letter
    slow_print(f"Welcome to {rainbow_name}", delay=0.01)
    print(Style.RESET_ALL + "\n")
    while True:
        option = int(input("Do you want to use the app with mobile?\n\n1. Yes\n2. No\n3. Exit App\n\n"))
        if option == 1:
            chat(app=True)
        elif option == 2:
            chat(app=None)
        elif option == 3:
            break
        else:
            print("Please enter a valid option.")
        