# Here we define the functions that execute the actions corresponding to each intent type 
# and the calls to tmdb API

import tmdb_api

from global_variables import *
from list_database import ListDatabase
from dialogue_state_tracker import DialogueStateTracker
from utils import Unsuccess

API_KEY = "037ff6ba26f3d5215cef3868aa3c8f73"
tmdb = tmdb_api.MovieDatabase(API_KEY)

# TODO: capire la gerarchia delle azioni, per esempio se c'è create list e add movie alla stessa intention, prima creo la lista e poi aggiungo il film
# TODO: fare l'azione di consiglia film e fare bene l'esecuzione delle print, tipo scrivere sure here is the list
# Execute one single action for one single intention
def execute(intention: dict, list_db: ListDatabase, dialogueST: DialogueStateTracker) -> str | Unsuccess:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in actions.execute")
        print("Executing intention:", intention)
    action_performed: str = ""
    intent_type = intention.get("intent")
    unsuccess: Unsuccess = Unsuccess()
    if intent_type == CREATE_NEW_LIST_INTENT:
        action_performed = createNewList(intention, list_db, dialogueST)
    elif intent_type == MODIFY_EXISTING_LIST_INTENT:
        action_performed = modifyList(intention, list_db)
        if intention.get("object_title") == action_performed: # no movie was found to add/remove
            unsuccess.add_no_movie(action_performed)
            intention.update({"object_title": None}) # reset the object title to None to ask again later
            return unsuccess
    elif intent_type == MOVIE_INFORMATION_REQUEST_INTENT:
        action_performed =  provideInfo(intention, list_db, dialogueST)
        if intention.get("object_title") == action_performed: # no movie/tv was found
            unsuccess.add_no_movie(action_performed)
            intention.update({"object_title": None}) # reset the object title to None to ask again later
            return unsuccess
    elif intent_type == SHOW_EXISTING_LIST_INTENT:
        action_performed = showExistingList(intention, list_db)
    elif intent_type == CANCEL_REQUEST_INTENT:
        action_performed = cancelRequest(intention, list_db, dialogueST)
    elif intent_type == OTHER_INTENT:
        other_request = handleOther(intention)
        unsuccess.add_other_request(other_request)
        intention["fulfilled"] = True # we consider other intent fulfilled after storing the request because the action is simply answering the user we can't do it
        return unsuccess
    else:
        print("Unknown intent type:", intent_type)
    intention["fulfilled"] = True
    return action_performed

# TODO: ricordarsi che se uno nella stessa intentions vuole creare una lista e aggiungere un film, 
# prima bisogna creare la lista e poi aggiungere il film (che va su modify list come intention)
def createNewList(intention: dict, list_db: ListDatabase, dialogueST: DialogueStateTracker) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in actions.createNewList")
    
    list_name: str = intention.get("list_name")
    if list_name.lower() not in list_db.lists:
        list_db.lists[list_name.lower()] = {}
        print(f"Created new list '{list_name}'.")
    else:
        turn: str = f"Movie Assistant: List '{list_name}' already exists, do you want to overwrite it? (type 'yes' or 'no')"
        print(turn)
        user_input: str = input("User: ")
        if (user_input.lower() == 'yes') or (user_input.lower() == 'y'):
            list_db.lists[list_name.lower()] = {}
            t: str = f"Overwritten existing list '{list_name}'."
            print(t)
            turn = turn + " " + t
        else:
            t: str = f"Did not overwrite existing list '{list_name}'."
            print(t)
            turn = turn + " " + t
        dialogueST.add_turn(turn)
    action_performed: str = f"{CREATE_NEW_LIST_INTENT} with list name '{list_name}'"
    return action_performed + ";"


def modifyList(intention: dict, list_db: ListDatabase) -> str:
    
    list_name: str = intention.get("list_name").lower()
    actions: list[str] = intention.get("action")
    object_title: str = intention.get("object_title")
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in actions.modifyList")
    if DEBUG:
        action_performed: str = f"{MODIFY_EXISTING_LIST_INTENT} with action '{action}' on list '{list_name}' and object title '{object_title}'"
        return action_performed
    
    for action in actions:
        if action == "add object":
            av_object: dict = tmdb.search_movies(object_title, num_results=1)[0] # av_object is audio video object, can be tv or movie
            list_db.lists[list_name][object_title] = av_object
            print(f"Added '{object_title}' to list '{list_name}'.")
        elif action == "remove object":
            if object_title in list_db.lists[list_name]:
                del list_db.lists[list_name][object_title]
                print(f"Removed '{object_title}' from list '{list_name}'.")
            else:
                print(f"'{object_title}' not found in list '{list_name}'.")
        elif action == "change title":
            new_title: str = intention.get("object_title").lower()
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
    
    action_performed: str = f"{MODIFY_EXISTING_LIST_INTENT} with action(s) '{actions}' on list '{list_name}' and object title '{object_title}'. "
    return action_performed + ";"

def provideInfo(intention: dict, list_db: ListDatabase, dialogueST: DialogueStateTracker) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in actions.provideInfo")
    object_title: str = intention.get("object_title")
    information_requested: list[str] = intention.get("information_requested")
    search_results: list[dict] = tmdb.search_titles(object_title, num_results=1)
    # If we don't find the movie, we return the title to inform the user later
    if not search_results:
        if DEBUG or DEBUG_LLM:
            print(f"No results found for '{object_title}'.")
        return object_title

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
        if DEBUG or DEBUG_LLM:
            print("No media details found, no action performed in provideInfo.")
        print(f"Movie Assistant: Could not retrieve details for '{object_title}'.")
        return ""
    
    turn: str = "Movie Assistant: Here is the information you requested for '" + object_title + "'."
    print(turn)
    if DEBUG or DEBUG_LLM:
        print(f"Information for '{object_title}':")
    for info in information_requested:
        if info == "get cast":
            if credits and credits.get('cast'):
                cast = credits.get('cast', [])
                t: str = "This is the cast of " + object_title + ": " + ", ".join([member['name'] for member in cast[:5]])
                print(t)
                turn = turn + " " + t
            else:
                print("Cast: Not available")
        elif info == "get director":
            if credits and credits.get('crew'):
                crew = credits.get('crew', [])
                directors = [member['name'] for member in crew if member.get('job') == 'Director']
                t: str = "This is the director(s) of " + object_title + ": " + ", ".join(directors)
                print(t)
                turn = turn + " " + t
            else:
                print(f"Director(s) for {object_title}: Not available")
        elif info == "get year":
            if media_type == "movie":
                release_date = media_details.get("release_date", "")
            else:  # tv
                release_date = media_details.get("first_air_date", "")
            year = release_date.split("-")[0] if release_date else "Unknown"
            t: str = f"The year {object_title} got out is {year}"
            print(t)
            turn = turn + " " + t
        elif info == "get genre":
            genres = [genre['name'] for genre in media_details.get("genres", [])]
            t: str = f"The genres of {object_title} are: " + ", ".join(genres) if genres else "Not available"
            print(t)
            turn = turn + " " + t
        elif info == "get ratings":
            rating = media_details.get("vote_average", "Unknown")
            t: str = f"The rating for {object_title} is: {rating}"
            print(t)
            turn = turn + " " + t
        elif info == "get plot":
            plot = media_details.get("overview", "No plot available.")
            t: str = f"The plot of {object_title} is: {plot}"
            print(t)
            turn = turn + " " + t
        elif info == "get duration":
            if media_type == "movie":
                duration = media_details.get("runtime", "Unknown")
                t: str = f"The duration of {object_title} is: " + (f"{duration} minutes" if duration != "Unknown" else "Unknown")
                print(t)
                turn = turn + " " + t
            else:  # tv
                seasons = media_details.get("number_of_seasons", "Unknown")
                episodes = media_details.get("number_of_episodes", "Unknown")
                t: str = f"{object_title} has {seasons} seasons and {episodes} episodes"
                print(t)
                turn = turn + " " + t
        else:
            print(f"Unknown information requested: '{info}'")
    
    action_performed: str = f"{MOVIE_INFORMATION_REQUEST_INTENT} for object title '{object_title}' with requested information {information_requested}"
    dialogueST.add_turn(turn)
    return action_performed + ";"

# TODO: controllare l'ordine di apparizione della stampa della lista e della risposta dell'LLM che dice ecco, ho fatto questa azione. Probabilmente sono al contrario
def showExistingList(intention: dict, list_db: ListDatabase) -> str:
    
    list_name: str = intention.get("list_name").lower()
    if DEBUG or DEBUG_LLM:
        print("DEBUG in actions.showExistingList")
    if DEBUG:
        print("lista stampata e va bene così")
        action_performed: str = f"{SHOW_EXISTING_LIST_INTENT} for list name '{list_name}'"
        return action_performed + ";"
    
    if "all" in list_name.lower():
        print("Showing all existing lists:")
        for lname, movie_list in list_db.lists.items():
            print(f"List '{lname}':")
            for title, details in movie_list.items():
                print(f"- {title}: {details}")
            print("")  # Blank line between lists
        action_performed: str = f"{SHOW_EXISTING_LIST_INTENT} for all lists"
        return action_performed + ";"
    else:
        movie_list: dict = list_db.get_list(list_name)
        if movie_list is not None:
            print(f"Contents of list '{list_name}':")
            for title, details in movie_list.items():
                print(f"- {title}: {details}")
        else:
            print(f"List '{list_name}' does not exist.")
            return 
    
    action_performed: str = f"{SHOW_EXISTING_LIST_INTENT} for list name '{list_name}'"
    return action_performed + ";"


def cancelRequest(intention: dict, list_db: ListDatabase, dialogueST: DialogueStateTracker) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in actions.cancelRequest")
    
    request_to_cancel: str = intention.get("request")
    if DEBUG or DEBUG_LLM:
        print(f"Cancelling request: {request_to_cancel}")
    
    updated_intentions: list[dict] = []
    removed: bool = False
    for intent in reversed(dialogueST.get_intentions_json()):
        if intent.get("intent") == request_to_cancel and not removed:
            removed = True        # skip this one only
            continue
        updated_intentions.append(intent)
    
    action_performed: str = f"{CANCEL_REQUEST_INTENT} for request '{request_to_cancel}'"
    return action_performed + ";"


# Simply return the text of the request
def handleOther(intention: dict) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in actions.handleOther")
    request: str = intention.get("text_of_the_request")
    if DEBUG or DEBUG_LLM:
        print(f"Handling other intent with request: {request}")
    return request

def successfulOutcome():
    pass      