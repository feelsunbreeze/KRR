from py2neo import Graph, Node, Relationship
import datetime
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from nltk.tag import pos_tag
import re
from colorama import Fore, Style
import pytholog as pl
import socket
# Neo4j 


def init_neo4j():
    return Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))

def get_relationship(predicate):
    word = word_tokenize(predicate)
    word = pos_tag(word)[0][1]
    if predicate.lower() == "has" or predicate == "have":
        return predicate.upper()
    elif word == "NNS":
        return predicate.upper()
    else:
        return f"IS_{predicate.upper()}_OF"
    

def clean_argument(argument):
    argument = argument.strip(").\"")
    return argument

def get_node_type(node):
    tagged = pos_tag([node])[0][1]
    node_type = "SocialNetwork" if tagged in ['NNP', 'NN'] else "SemanticNetwork"
    return node_type

def create_node(rule_or_fact):
    if ":-" in rule_or_fact: 
        rule, _ = rule_or_fact.split(":-")
        name, _ = rule.split("(")
        relationship = get_relationship(name)
        results = kb.query(pl.Expr(rule))
        if 'No' in results:
            print(Fore.LIGHTRED_EX + f'\'{rule}\' rule raised an error. Re-check the prolog logic.' + Style.RESET_ALL)
            return
        subjects = []
        subjects2 = []
        for result in results:
            subjects.append(result['X'].capitalize())
            subjects2.append(result['Y'].capitalize())

        while subjects:
            subject = subjects[0]
            subject2 = subjects2[0]
            node_type1 = get_node_type(subject)
            node_type2 = get_node_type(subject2)
            try:
                query = f"""
                MERGE (a:{node_type1} {{name: '{subject}'}})
                MERGE (b:{node_type2} {{name: '{subject2}'}})
                MERGE (a)-[r:{relationship}]->(b)
                """
            except Exception as e:
                print(e)
            try:
                graph.run(query)
            except Exception as e:
                print(e)
            subjects.pop(0)
            subjects2.pop(0)    

    else:  # If it's a Prolog fact
        predicate, argument = re.match(r'(\w+)\((.*)\)', rule_or_fact).groups()
        # If it's a single argument fact.
        if "," not in rule_or_fact:
            argument = clean_argument(argument)
            node_type = get_node_type(argument)
            argument = argument.capitalize()
            query = f"""
            MERGE (a:{node_type} {{name: '{argument}'}})
            MERGE (b:SemanticNetwork {{name: '{predicate}'}})
            MERGE (a)-[r:IS_A]->(b)
            """
        else: # If it's a relationship statement.
            argument1, argument2 = map(clean_argument, argument.split(", "))
            node_type1 = get_node_type(argument1)
            node_type2 = get_node_type(argument2)
            argument1 = argument1.capitalize()
            argument2 = argument2.capitalize()
            predicate = get_relationship(predicate)
            query = f"""
            MERGE (a:{node_type1} {{name: '{argument1}'}})
            MERGE (b:{node_type2} {{name: '{argument2}'}})
            MERGE (a)-[r:{predicate}]->(b)
            """

    graph.run(query)

def fetch_relationship_data_from_neo4j(relationship, name):
    if relationship == "have" or relationship == "has":
        relationship = relationship.upper()
    else:
        relationship = f"IS_{relationship.upper()}_OF"

    query = f"""
        MATCH (a)-[r:{relationship}]-(b)
        WHERE a.name = "{name}"
        RETURN a.name as start_node, type(r) as relationship, b.name as end_node
    """
    result = graph.run(query)
    data = []
    for record in result:
        data.append({
            "start_node": record["start_node"],
            "relationship": record["relationship"],
            "end_node": record["end_node"]
        })
    if data:
        return data
    return "nope"

def fetch_all_data_from_neo4j(name):
    if name == None:
        return None
    
    query = f"""
        MATCH (n:SocialNetwork {{name: "{name}"}})-[r]-(related)
        RETURN startNode(r) as start, endNode(r) as end, type(r) as type
    """
    result = graph.run(query)
    data = []
    for record in result:
        data.append({
            "start_node": record["start"],
            "end_node": record["end"],
            "relationship_type": record["type"]
        })
    return data

# Pytholog Helper 
def process_line(line):
    processed_line = ''
    prev_end = 0
    for match in re.finditer(r'\b[A-Za-z]\b', line):
        start = match.start()
        end = match.end()
        processed_line += line[prev_end:start] + line[start:end].upper()
        prev_end = end
    processed_line += line[prev_end:]
    return processed_line
# Pytholog 

def import_prolog_file(file_path):
    prolog_queries = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('%'):
                if ":-" in line:
                    line = process_line(line)
                else:
                    line = line.lower()
                line = line.replace('.', '')  # This line removes any full stop in the line
                prolog_queries.append(line)
    return prolog_queries

# Helper 
def to_natural_language(data):
    sentences = []
    for record in data:
        start_node_name = record["start_node"]["name"]
        end_node_name = record["end_node"]["name"]
        relationship_type = record["relationship_type"]
        relationship_words = relationship_type.split("_")
        relationship_type = " ".join(relationship_words)
        sentence = f"{start_node_name} {relationship_type.lower()} {end_node_name}"
        sentences.append(sentence)
    sentences.reverse()
    return sentences

def get_definition(word):
    synsets = wordnet.synsets(word)
    if synsets:
        return synsets[0].definition()
    else:
        return None

def capitalize_last_word(sentences):
    modified_sentences = []
    for sentence in sentences:
        words = sentence.split()  
        last_word = words[-1]     
        capitalized_last_word = last_word.capitalize()  
        words[-1] = capitalized_last_word  
        modified_sentence = ' '.join(words) 
        modified_sentences.append(modified_sentence)
    return modified_sentences

def get_song_location(song_name, artist):
    song_name = ' '.join(element.capitalize() for element in song_name.split())
    artist = artist.capitalize()
    print(song_name, artist)
    query = f"""
    MATCH (n:Song {{title: "{song_name}", artist: "{artist}"}})
    RETURN n.location
    """
    result = graph.run(query)
    location = [record["n.location"] for record in result]
    print(location[0])
    return location[0]

def get_sentiment(words):
    if '?' in words:
        return "Question"
    elif '!' in words:
        return "Exclamation"
    else:
        return "Statement"

def create_conversation_node(text):
    words = word_tokenize(text)
    sentiment = get_sentiment(words)
    conversation_node = Node(
        "Conversation",
        text=text,
        date=datetime.date.today(),
        time=datetime.datetime.now().time(),
        ip=IP,
        sentiment=sentiment
    )
    graph.create(conversation_node)

    previous_word_node = None
    for word in words:
        if word == '?' or word == "!":
            continue
        word_node = Node("Word", text=word)
        graph.create(word_node)

        relationship = Relationship(conversation_node, "CONTAINS", word_node)
        graph.create(relationship)

        if previous_word_node is not None:
            next_relationship = Relationship(previous_word_node, "NEXT", word_node)
            graph.create(next_relationship)

        previous_word_node = word_node


def create_episodic_memory(input_text, response_text):
    sentiment = get_sentiment(input_text)
    episodic_node = Node("Episodic", text=input_text, date=datetime.date.today(),
        time=datetime.datetime.now().time(),
        ip=IP,
        sentiment=sentiment)
    graph.create(episodic_node)

    response_node = Node("Response", text=response_text)
    graph.create(response_node)

    # Create a relationship between episodic_node and response_node
    relationship = Relationship(episodic_node, "ANSWERED", response_node)
    graph.create(relationship)


def process_sentence_for_neo4j(subject, verb, obj):
    query = f"""
                MERGE (a:{get_node_type(subject)} {{name: '{subject}'}})
                MERGE (b:{get_node_type(obj)} {{name: '{obj}'}})
                MERGE (a)-[r:{verb.upper()}]->(b)
                """
    graph.run(query)

def start_neo4j():
    global graph, kb
    try:
        graph = init_neo4j()
        if graph is None:
            raise Exception(f"Error initializing Neo4j. Make sure it's running.")
    except Exception as e:
        raise Exception(f"Error initializing Neo4j. Make sure it's running. {e}")


def init_backend(file_name=None):
    global kb
    if file_name != None:
        try:
            prolog_data = import_prolog_file(file_name)
            if prolog_data is None:
                raise Exception(f"Invalid file.")    
        except Exception as e:
            raise Exception(f"Error importing prolog file. Make sure it's in the same folder and you provided the correct name. {e}")
        
        kb = pl.KnowledgeBase("kb")
        kb(prolog_data)
        for data in prolog_data:
            create_node(data.strip())

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

IP = get_ip()