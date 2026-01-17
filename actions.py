# Here we define the functions that execute the actions corresponding to each intent type 
# and the calls to tmdb API

import tmdb_api
import utils

from global_variables import *
from list_database import ListDatabase
from dialogue_state_tracker import DialogueStateTracker

API_KEY = "037ff6ba26f3d5215cef3868aa3c8f73"
tmdb = tmdb_api.MovieDatabase(API_KEY)

# TODO: fare l'azione di consiglia film
# Execute one single action for one single intention
def execute(intention: dict, list_db: ListDatabase, dialogueST: DialogueStateTracker) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in actions.execute")
        print("Executing intention:", intention)
    action_performed: str = ""
    intent_type = intention.get("intent")
    if intent_type == CREATE_NEW_LIST_INTENT:
        action_performed = createNewList(intention, list_db, dialogueST)
    elif intent_type == MODIFY_EXISTING_LIST_INTENT:
        action_performed = modifyList(intention, list_db)
    elif intent_type == MOVIE_INFORMATION_REQUEST_INTENT:
        action_performed =  provideInfo(intention, list_db)
    elif intent_type == SHOW_EXISTING_LIST_INTENT:
        action_performed = showExistingList(intention, list_db)
    elif intent_type == OTHER_INTENT:
        action_performed = handleOther(intention)
    else:
        print("Unknown intent type:", intent_type)
    
    return action_performed + ";"

# TODO: ricordarsi che se uno nella stessa intentions vuole creare una lista e aggiungere un film, 
# prima bisogna creare la lista e poi aggiungere il film (che va su modify list come intention)
def createNewList(intention: dict, list_db: ListDatabase, dialogueST: DialogueStateTracker) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in actions.createNewList")
    
    list_name: str = intention.get("list_name")
    if list_name not in list_db.lists:
        list_db.lists[list_name] = {}
        print(f"Created new list '{list_name}'.")
    else:
        turn: str = f"Movie Assistant: List '{list_name}' already exists, do you want to overwrite it? (type 'yes' or 'no')"
        print(turn)
        user_input: str = input("User: ")
        if (user_input.lower() == 'yes') or (user_input.lower() == 'y'):
            list_db.lists[list_name] = {}
            t: str = f"Overwritten existing list '{list_name}'."
            print(t)
            turn = turn + " " + t
        else:
            t: str = f"Did not overwrite existing list '{list_name}'."
            print(t)
            turn = turn + " " + t
        dialogueST.add_turn(turn)
    action_performed: str = f"{CREATE_NEW_LIST_INTENT} with list name '{list_name}'"
    return action_performed


def modifyList(intention: dict, list_db: ListDatabase) -> str:
    
    list_name: str = intention.get("list_name")
    action: str = intention.get("action")
    object_title: str = intention.get("object_title")
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in actions.modifyList")
    if DEBUG:
        action_performed: str = f"{MODIFY_EXISTING_LIST_INTENT} with action '{action}' on list '{list_name}' and object title '{object_title}'"
        return action_performed
    
    if action == "add object":
        av_object: dict = tmdb.search_movies(object_title, num_results=1)[0] # av_object is audio video object
        list_db.lists[list_name][object_title] = av_object
        print(f"Added '{object_title}' to list '{list_name}'.")
    elif action == "remove object":
        if object_title in list_db.lists[list_name]:
            del list_db.lists[list_name][object_title]
            print(f"Removed '{object_title}' from list '{list_name}'.")
        else:
            print(f"'{object_title}' not found in list '{list_name}'.")
    elif action == "change title":
        new_title: str = intention.get("object_title")
        if list_name in list_db.lists:
            list_db.lists[new_title] = list_db.lists.pop(list_name)
            print(f"Changed list title from '{list_name}' to '{new_title}'.")
        else:
            print(f"List '{list_name}' does not exist.")
    elif action == "delete list":
        if list_name in list_db.lists:
            del list_db.lists[list_name]
            print(f"Deleted list '{list_name}'.")
        else:
            print(f"List '{list_name}' does not exist.")
    else:
        print(f"Unknown action '{action}' for modifying list.") 
    
    action_performed: str = f"{MODIFY_EXISTING_LIST_INTENT} with action '{action}' on list '{list_name}' and object title '{object_title}'. "
    return action_performed

def provideInfo(intention: dict, list_db: ListDatabase) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in actions.provideInfo")
    
    object_title: str = intention.get("object_title")
    information_requested: list[str] = intention.get("information_requested")
    
    search_results: list[dict] = tmdb.search_titles(object_title, num_results=1)
    if not search_results:
        print(f"No results found for '{object_title}'.")
        return ""
    
    media: dict = search_results[0]  # Take the first search result
    media_id: int = media.get("id")
    media_type: str = media.get("type")
    
    if media_type == "movie":
        media_details: dict = tmdb._get_movie_details(media_id)
        credits: dict = tmdb._get_movie_credits(media_id)
    elif media_type == "tv":
        media_details: dict = tmdb._get_tv_details(media_id)
        credits = None  # TV shows would need _get_tv_credits if that method existed
    else:
        print(f"Unknown media type for '{object_title}'.")
        return "unknown media type"
    
    if not media_details:
        print(f"Could not retrieve details for '{object_title}'.")
        return ""
    
    print(f"Information for '{object_title}':")
    for info in information_requested:
        if info == "get cast":
            if credits and credits.get('cast'):
                cast = credits.get('cast', [])
                print("Cast:", ", ".join([member['name'] for member in cast[:5]]))
            else:
                print("Cast: Not available")
        elif info == "get director":
            if credits and credits.get('crew'):
                crew = credits.get('crew', [])
                directors = [member['name'] for member in crew if member.get('job') == 'Director']
                print("Director(s):", ", ".join(directors) if directors else "Not available")
            else:
                print("Director(s): Not available")
        elif info == "get year":
            if media_type == "movie":
                release_date = media_details.get("release_date", "")
            else:  # tv
                release_date = media_details.get("first_air_date", "")
            year = release_date.split("-")[0] if release_date else "Unknown"
            print("Year:", year)
        elif info == "get genre":
            genres = [genre['name'] for genre in media_details.get("genres", [])]
            print("Genres:", ", ".join(genres) if genres else "Not available")
        elif info == "get ratings":
            rating = media_details.get("vote_average", "Unknown")
            print("Rating:", rating)
        elif info == "get plot":
            plot = media_details.get("overview", "No plot available.")
            print("Plot:", plot)
        elif info == "get duration":
            if media_type == "movie":
                duration = media_details.get("runtime", "Unknown")
                print("Duration:", f"{duration} minutes" if duration != "Unknown" else "Unknown")
            else:  # tv
                seasons = media_details.get("number_of_seasons", "Unknown")
                episodes = media_details.get("number_of_episodes", "Unknown")
                print("Duration:", f"{seasons} seasons, {episodes} episodes")
        else:
            print(f"Unknown information requested: '{info}'")
    
    action_performed: str = f"{MOVIE_INFORMATION_REQUEST_INTENT} for object title '{object_title}' with requested information {information_requested}"
    return action_performed

# TODO: controllare l'ordine di apparizione della stampa della lista e della risposta dell'LLM che dice ecco, ho fatto questa azione. Probabilmente sono al contrario
def showExistingList(intention: dict, list_db: ListDatabase) -> str:
    
    list_name: str = intention.get("list_name")
    if DEBUG or DEBUG_LLM:
        print("DEBUG in actions.showExistingList")
    if DEBUG:
        print("lista stampata e va bene così")
        action_performed: str = f"{SHOW_EXISTING_LIST_INTENT} for list name '{list_name}'"
        return action_performed
    
    movie_list: dict = list_db.get_list(list_name)
    if movie_list is not None:
        print(f"Contents of list '{list_name}':")
        for title, details in movie_list.items():
            print(f"- {title}: {details}")
    else:
        print(f"List '{list_name}' does not exist.")
    
    action_performed: str = f"{SHOW_EXISTING_LIST_INTENT} for list name '{list_name}'"
    return action_performed

# Simply return the text of the request
def handleOther(intention: dict) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in actions.handleOther")
    request: str = intention.get("text_of_the_request")
    if DEBUG or DEBUG_LLM:
        print(f"Handling other intent with request: {request}")
    return request