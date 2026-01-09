# The dialogue manager chooses the next best action TODO aggiungi una descrizione migliore (è anche quello che chiama le API secondo GPT)

import subprocess
import time
import os
import json
import utils
import actions
import natural_language_generator as nlg
import natural_language_understander as nlu

from list_database import ListDatabase
from dialogue_state_tracker import DialogueStateTracker
from global_variables import *

# We respond to the user. First we must understand what is null in the json intentions. Then we must understand 
# if we can fill the nulls with the current information or if we need more information (that we will ask 
# to the the user), then we generate an appropriate response
def followupInteraction(dialogueST: DialogueStateTracker, list_db: ListDatabase, process: subprocess.Popen):

    try:
        print("JSON intentions:", dialogueST.get_intentions_json())
    except Exception as e:
        print(f"Error: An unexpected error occurred during printing JSON intentions: {e}")
        exit(1)
    # We check if there are intentions with no null slots that we can fulfill directly
    fulfillIntent(dialogueST, list_db)
    
    # If there are null slots in the json, we need to fill them. We ask the LLM to do it for us
    if(any(None in intention.values() for intention in dialogueST.get_intentions_json())): # we search for None instead of null because of python json format
        print("There are null slots to fill, we will ask the LLM to fill them.")
        user_response: str | None = fillNullSlots(dialogueST, process)
        fulfillIntent(dialogueST, list_db)
        # After filling the null slots, we check if there are new intentions from the user response
        if user_response:
            nlu.checkForIntention(process, dialogueST)
    else:
        print("No null slots to fill, so the request is satisfied.")
    return

def fillNullSlots(dialogueST: DialogueStateTracker, process: subprocess.Popen) -> str | None:

    # First we try to fill the null slots with the current information
    filled_json: list[dict] = fillWithCurrentInfo(process, dialogueST)
    dialogueST.update_intentions_json(filled_json)
    # Check if there are still null slots
    if (any(None in intention.values() for intention in dialogueST.get_intentions_json())):
        print("There are still null slots to fill, we will ask the user for more information.")
        instruction: str = nlg.generate_question(dialogueST, filled_json)
        userResponse: str = askUser(process, instruction)
        dialogueST.update_last_user_input(userResponse)
        dialogueST.add_turn(userResponse)
        print("User response received: ", userResponse)
        # Now the user answer is part of our current info
        filled_json = fillWithCurrentInfo(process, dialogueST)
        dialogueST.update_intentions_json(filled_json)
        print("Filled JSON after asking user: ", filled_json)
        return userResponse
    else:
        print("All null slots have been filled.")
        return None

def askUser(process: subprocess.Popen, instruction: str) -> str:
    llmAnswer: str = utils.askAndReadAnswer(process, instruction)
    print("LLM asks the user:", llmAnswer)
    userInput: str = input()
    return userInput

def fillWithCurrentInfo(process: subprocess.Popen, dialogueST: DialogueStateTracker) -> list[dict]:
    # Load the last N turns of the conversation from the dialogue state tracker
    last_N_turns: list[str] = dialogueST.get_last_N_turns()
    last_N_turns: str = "  ".join(last_N_turns)
    json_to_fill: str = json.dumps(dialogueST.get_intentions_json(), indent=2) # TODO: In caso non funzionasse c'è la funzione jsonToString in utils.py che trasforma una lista di dict in una stringa json
    instruction: str = f"""You are a movie list assistant and movie expert, you can help the user only {MODIFY_EXISTING_LIST_INTENT}, {CREATE_NEW_LIST_INTENT} or answering to his {MOVIE_INFORMATION_REQUEST_INTENT}. This is the content of your previous conversation with the user: {last_N_turns}. Use the content of that conversation to fill the null slots inside this json: {json_to_fill}. For the {MODIFY_EXISTING_LIST_INTENT}, these are the only action possible: {MODIFY_LIST_ACTIONS}. For the {MOVIE_INFORMATION_REQUEST_INTENT}, these are the only action possible: {MOVIE_INFO_ACTIONS}. If you don't find the information to fill a slot, leave it as null. Print ONLY the same JSON string, but with the nulls that you can fill, filled, in a JSON format and NOTHING ELSE after."""
    filled_json: str = utils.askAndReadAnswer(process, instruction)
    print("Filled JSON received: ", filled_json)
    filled_json_list : list[dict] = utils.stringToJson(filled_json)
    return filled_json_list

def fulfillIntent(dialogueST: DialogueStateTracker, list_db: ListDatabase):
    for intention in dialogueST.get_intentions_json():
        if None not in intention.values() and intention.get("fulfilled") == False:
            actions.execute(intention, list_db) # do the correspondent action for each intention, like printing a list or call an API for movie info ecc.
            intention["fulfilled"] = True
    # Remove the fulfilled intentions from the list
    unfulfilled_intentions: list[dict] = [intent for intent in dialogueST.get_intentions_json() if intent.get("fulfilled") == False]
    dialogueST.update_intentions_json(unfulfilled_intentions)