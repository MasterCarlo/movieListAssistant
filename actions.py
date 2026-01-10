# Here we define the functions that execute the actions corresponding to each intent type 
# and the calls to tmdb API

import tmdb_api
import utils

from global_variables import *
from list_database import ListDatabase
from dialogue_state_tracker import DialogueStateTracker

API_KEY = "037ff6ba26f3d5215cef3868aa3c8f73"
tmdb = tmdb_api.MovieDatabase(API_KEY)

# Execute one single action for one single intention
def execute(intention: dict, list_db: ListDatabase, dialogueST: DialogueStateTracker) -> str:
    
    action_performed: str = ""
    intent_type = intention.get("intent")
    if intent_type == CREATE_NEW_LIST_INTENT:
        action_performed = createNewList(intention, list_db)
    elif intent_type == MODIFY_EXISTING_LIST_INTENT:
        action_performed = modifyList(intention, list_db)
    elif intent_type == MOVIE_INFORMATION_REQUEST_INTENT:
        action_performed =  provideInfo(intention, list_db)
    elif intent_type == SHOW_EXISTING_LIST_INTENT:
        action_performed = showExistingList(intention, list_db)
    elif intent_type == OTHER_INTENT:
        action_performed = fallbackPolicy(intention, list_db)
    else:
        print("Unknown intent type:", intent_type)
    
    return action_performed

# TODO: ricordarsi che se uno nella stessa intentions vuole creare una lista e aggiungere un film, 
# prima bisogna creare la lista e poi aggiungere il film (che va su modify list come intention)
def createNewList(intention: dict, list_db: ListDatabase) -> str:
    
    
    list_name: str = intention.get("list_name")
    if list_name not in list_db.lists:
        list_db.lists[list_name] = {}
        print(f"Created new list '{list_name}'.")
    else:
        print(f"List '{list_name}' already exists, do you want to overwrite it? (type 'yes' or 'no')")
        user_input: str = input()
        if (user_input.lower() == 'yes') or (user_input.lower() == 'y'):
            list_db.lists[list_name] = {}
            print(f"Overwritten existing list '{list_name}'.")
        else:
            print(f"Did not overwrite existing list '{list_name}'.")
    
    action_performed: str = f"{CREATE_NEW_LIST_INTENT} with list name '{list_name}'. "
    return action_performed


def modifyList(intention: dict, list_db: ListDatabase) -> str:
    
    list_name: str = intention.get("list_name")
    action: str = intention.get("action")
    object_title: str = intention.get("object_title")
    
    if action == "add object":
        av_object: dict = tmdb.search_movies(object_title, num_results=3)[0] # av_object is audio video object
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
    
    object_title: str = intention.get("object_title")
    information_requested: list[str] = intention.get("information_requested")
    
    search_results: list[dict] = tmdb.search_titles(object_title, num_results=3)
    if not search_results:
        print(f"No results found for '{object_title}'.")
        return
    
    media: dict = search_results[0]  # Take the first search result
    media_id: int = media.get("id")
    if media.get("media_type") == "movie":
        media_details: dict = tmdb._get_movie_details(media_id)
    elif media.get("media_type") == "tv":
        media_details: dict = tmdb._get_tv_details(media_id)
    else:
        print(f"Unknown media type for '{object_title}'.")
        return
    
    print(f"Information for '{object_title}':")
    for info in information_requested:
        if info == "get cast":
            cast = tmdb.get_movie_cast(media_id)
            print("Cast:", ", ".join([member['name'] for member in cast[:5]]))  # Print top 5 cast members
        elif info == "get director":
            crew = tmdb.get_movie_crew(media_id)
            directors = [member['name'] for member in crew if member['job'] == 'Director']
            print("Director(s):", ", ".join(directors))
        elif info == "get year":
            release_date = media_details.get("release_date", "Unknown")
            year = release_date.split("-")[0] if release_date != "Unknown" else "Unknown"
            print("Year:", year)
        elif info == "get genre":
            genres = [genre['name'] for genre in media_details.get("genres", [])]
            print("Genres:", ", ".join(genres))
        elif info == "get ratings":
            rating = media_details.get("vote_average", "Unknown")
            print("Rating:", rating)
        elif info == "get plot":
            plot = media_details.get("overview", "No plot available.")
            print("Plot:", plot)
        elif info == "get duration":
            duration = media_details.get("runtime", "Unknown")
            print("Duration:", f"{duration} minutes" if duration != "Unknown" else "Unknown")
        else:
            print(f"Unknown information requested: '{info}'")
    
    action_performed: str = f"{MOVIE_INFORMATION_REQUEST_INTENT} for object title '{object_title}' with requested information {information_requested}. "
    return action_performed

def showExistingList(intention: dict, list_db: ListDatabase) -> str:
    
    list_name: str = intention.get("list_name")
    movie_list: dict = list_db.get_list(list_name)
    if movie_list is not None:
        print(f"Contents of list '{list_name}':")
        for title, details in movie_list.items():
            print(f"- {title}: {details}")
    else:
        print(f"List '{list_name}' does not exist.")
    
    action_performed: str = f"{SHOW_EXISTING_LIST_INTENT} for list name '{list_name}'. "
    return action_performed

# TODO: dopo aver eseguito ogni azione bisogna informare l'utente quindi chiamare l'llm
def fallbackPolicy(intention: dict, list_db: ListDatabase) -> str:
    
    request: str = "The text of the request is " + intention.get("text_of_the_request")
    print(f"Handling other intent with request: {request}")
    instruction: str = "The user also has made a request that exceeds your expertise. Please politely inform the user that you are unable to assist with that particular request." + request + ". Then, remind the user that you can help him with" + MODIFY_EXISTING_LIST_INTENT + ", " + CREATE_NEW_LIST_INTENT + " or answering to his " + MOVIE_INFORMATION_REQUEST_INTENT + "." 
    return instruction