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

    if DEBUG or DEBUG_LLM:
        print("JSON intentions in followupInteraction")
    # First we fill the intentions json with our current info
    filled_json: list[dict] = fillWithCurrentInfo(process, dialogueST)
    dialogueST.update_intentions(filled_json)
    # We check if there are intentions with no null slots that we can fulfill directly. We register the actions performed
    actions_performed: str = ""
    other_request: str = ""
    actions_performed, other_request = fulfillIntent(dialogueST, list_db)
    dialogueST.update_actions(actions_performed) # update the action performed so far
    
    # Now we check if there are still intentions to fulfill, it means the intention_json is uncomplete (it has null slots)
    if(any(False in intention.values() for intention in dialogueST.get_intentions_json())): 
        # If there are null slots in the json, we need to fill them
        if(any(None in intention.values() for intention in dialogueST.get_intentions_json())): # we search for None instead of null because of python json format
            print("There are null slots to fill, we will ask the LLM to fill them.")
            user_response: str | None = fillNullSlots(dialogueST, process, other_request)
            result: tuple[str, str] = fulfillIntent(dialogueST, list_db)
            actions_performed = actions_performed + result[0]
            other_request = other_request + result[1]
            dialogueST.update_actions(actions_performed)
            # After filling the null slots, we check if there are new intentions from the user response.
            # In the next interaction we will take care of them if present
            if user_response:
                nlu.checkForIntention(process, dialogueST)
        else:
            print("No null slots to fill")
    else: # All intentions have been fulfilled
        if DEBUG or DEBUG_LLM:
            print("All intentions have been fulfilled.")
        instruction: str = nlg.communicateCompletion(dialogueST, other_request)
        dialogueST.clear_actions() # we clear the actions performed for the next interactions
        llmAnswer: str = utils.askAndReadAnswer(process, instruction) # we tell the LLM to inform the user that all his requests have been satisfied
        if DEBUG or DEBUG_LLM:
            print("LLM informs the user:", llmAnswer)
        dialogueST.add_turn("Movie Assistant: " + llmAnswer)
    return

def fillNullSlots(dialogueST: DialogueStateTracker, process: subprocess.Popen, other_request: str) -> str | None:

    if DEBUG or DEBUG_LLM:
        print("DEBUG in fillNullSlots.")
    # Check if there are still null slots
    if (any(None in intention.values() for intention in dialogueST.get_intentions_json())):
        userResponse: str = ""
        userResponse = askUser(process, dialogueST, other_request)
        if DEBUG or DEBUG_LLM:
            print("User response received in fillNullSlots: ", userResponse)
        # Now the user answer is part of our current info
        filled_json = fillWithCurrentInfo(process, dialogueST)
        dialogueST.update_intentions(filled_json)
        if DEBUG or DEBUG_LLM:
            print("Filled JSON after asking user in fillNullSlots: ", filled_json)
        return userResponse
    else:
        print("All null slots have been filled.")
        return None

def askUser(process: subprocess.Popen, dialogueST: DialogueStateTracker, other_request: str) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in askUser")
    instruction: str = ""
    # We generate the question for the user for more information. Inside the question there is also the 
    # communication of previously performed actions or failure to fulfill something out of boundaries
    instruction= nlg.generateLLMResponse(dialogueST, other_request)
    llmAnswer: str = utils.askAndReadAnswer(process, instruction) # the LLM actually asks the user something. It also communicate any action performed so far and any fallback policy (if the user requested something outside the boundaries of the system)
    # If the user had an other intent, we already answered him that we can't handle it, 
    # so we fulfilled it. We mark it as fulfilled so we don't ask again later
    for intention in dialogueST.get_intentions_json(): #it's for safety, should be already fulfilled
        if intention.get("intent") == OTHER_INTENT:
            intention["fulfilled"] = True
    dialogueST.add_turn("Movie Assistant: " + llmAnswer)
    if DEBUG or DEBUG_LLM:
        print("LLM asks the user:", llmAnswer)
    userInput: str = input()
    dialogueST.update_last_user_input(userInput)
    dialogueST.add_turn("User: " + userInput)
    return userInput

def fillWithCurrentInfo(process: subprocess.Popen, dialogueST: DialogueStateTracker) -> list[dict]:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in fillWithCurrentInfo.")
    # Load the last N turns of the conversation from the dialogue state tracker
    last_N_turns: list[str] = dialogueST.get_last_N_turns()
    last_N_turns: str = "  ".join(last_N_turns)
    json_to_fill: str = json.dumps(dialogueST.get_intentions_json(), indent=2) # TODO: In caso non funzionasse c'è la funzione jsonToString in utils.py che trasforma una lista di dict in una stringa json
    instruction: str = f"""You are a movie list assistant and movie expert, you can help the user only {MODIFY_EXISTING_LIST_INTENT}, {CREATE_NEW_LIST_INTENT} or answering to his {MOVIE_INFORMATION_REQUEST_INTENT}. This is the content of your previous conversation with the user: {last_N_turns}. Use the content of that conversation to fill the null slots inside this json: {json_to_fill}. For the {MODIFY_EXISTING_LIST_INTENT}, these are the only action possible: {MODIFY_LIST_ACTIONS}. For the {MOVIE_INFORMATION_REQUEST_INTENT}, these are the only actions possible: {MOVIE_INFO_ACTIONS}. Be aware of typing errors of the user.If you don't find the information to fill a slot, leave it as null. Print ONLY the same JSON string, but with the nulls that you can fill, filled, in a JSON format and NOTHING ELSE after."""
    filled_json: str = utils.askAndReadAnswer(process, instruction)
    if DEBUG or DEBUG_LLM:
        print("Filled JSON received in fillWithCurrentInfo: ", filled_json)
    filled_json_list : list[dict] = utils.stringToJson(filled_json)
    dialogueST.update_intentions(filled_json_list)
    return filled_json_list

# If there are intentions with no null slots, we fulfill them directly
def fulfillIntent(dialogueST: DialogueStateTracker, list_db: ListDatabase) -> tuple[str, str]:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in fulfillIntent.")
    other_request: str = "" # This is needed ONLY to create the answer for the fallback policy
    actions_performed: str = "" # A written report of what action the LLM has completed
    for intention in dialogueST.get_intentions_json(): 
        if None not in intention.values() and intention.get("fulfilled") == False:
            if intention.get("intent") == OTHER_INTENT:
                # Simply return the text of the other request for later use in fallback policy
                other_request = other_request + "; " + actions.execute(intention, list_db, dialogueST)
                intention["fulfilled"] = True
            else:
                actions_performed = actions_performed + actions.execute(intention, list_db, dialogueST) # do the correspondent action for each intention, like printing a list or call an API for movie info ecc.
                intention["fulfilled"] = True
    # Remove the fulfilled intentions from the list
    unfulfilled_intentions: list[dict] = [intent for intent in dialogueST.get_intentions_json() if intent.get("fulfilled") == False]
    dialogueST.update_intentions(unfulfilled_intentions)
    return actions_performed, other_request