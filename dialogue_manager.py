# The dialogue manager chooses the next best action TODO aggiungi una descrizione migliore (è anche quello che chiama le API secondo GPT)

import json
import subprocess
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
    other_request: str = fillWithCurrentInfo(process, dialogueST)
    # We check if there are intentions with no null slots that we can fulfill directly. We register the actions performed
    actions_performed: str = ""
    no_movie: list[str] = []
    other: str = ""
    actions_performed, no_movie, other = fulfillIntent(dialogueST, list_db)
    other_request = other_request + other # this is for intention outside of our domain
    dialogueST.update_actions(actions_performed) # update the action performed so far
    
    # Now we check if there are still intentions to fulfill, it means the intention_json is uncomplete (it has null slots)
    if(any(False in intention.values() for intention in dialogueST.get_intentions_json())): 
        # If there are null slots in the json, we need to fill them
        if(any(None in intention.values() for intention in dialogueST.get_intentions_json())): # we search for None instead of null because of python json format
            print("There are null slots to fill, we will ask the LLM to fill them.")
            user_response: str | None = fillNullSlots(dialogueST, process, no_movie, other_request)
            result: tuple[str, list[str], str] = fulfillIntent(dialogueST, list_db)
            actions_performed = actions_performed + result[0]
            dialogueST.update_actions(actions_performed)
            # After filling the null slots, we check if there are new intentions from the user response.
            # If present, in the next interaction we will take care of them
            if user_response:
                nlu.checkForIntention(process, dialogueST )
        else:
            print("No null slots to fill")
    else: # All intentions have been fulfilled
        if DEBUG or DEBUG_LLM:
            print("All intentions have been fulfilled.")
        instruction: str = nlg.communicateCompletion(dialogueST, other_request)
        dialogueST.clear_actions() # we clear the actions performed for the next interactions
        llmAnswer: str = utils.askAndReadAnswer(process, instruction) # we tell the LLM to inform the user that all his requests have been satisfied
        print("Movie Assistant:", llmAnswer)
        dialogueST.add_turn("Movie Assistant: " + llmAnswer)
        user_response: str = input("User: ")
        dialogueST.update_last_user_input(user_response)
        dialogueST.add_turn("User: " + user_response)
        nlu.checkForIntention(process, dialogueST )
    return


def fillWithCurrentInfo(process: subprocess.Popen, dialogueST: DialogueStateTracker) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in fillWithCurrentInfo.")
        print("Current intentions JSON to fill:", utils.jsonToString(dialogueST.get_intentions_json()))
    # Get the last N turns of the conversation from the dialogue state tracker
    last_N_turns: list[str] = dialogueST.get_last_N_turns()
    last_N_turns: str = "  ".join(last_N_turns)
    json_to_fill: str = utils.jsonToString(dialogueST.get_intentions_json()) # We need one line json because shell can't manage multi line text
    instruction: str = f"""You are a movie list assistant, you can help the user only {MODIFY_EXISTING_LIST_INTENT}, {CREATE_NEW_LIST_INTENT}, {CANCEL_REQUEST_INTENT} or answering to his {MOVIE_INFORMATION_REQUEST_INTENT}. The [{CANCEL_REQUEST_INTENT}] intention is hard to catch, it's rarely explicit: if the user say something like "never mind", "I don't care anymore", "go on", "don't worry" etc., probably he wants to cancel his previous request. For the {MODIFY_EXISTING_LIST_INTENT}, these are the only action possible: {MODIFY_LIST_ACTIONS}. If the action is even slightly different from these ones, the intent has to be considered [{OTHER_INTENT}]. For the {MOVIE_INFORMATION_REQUEST_INTENT}, these are the only info requests possible: {MOVIE_INFO_ACTIONS}. If the info request is even slightly different from these ones, the intent has to be considered {OTHER_INTENT}. This is the content of your previous conversation with the user:" {last_N_turns}". Use the content of that conversation to fill the null slots inside this json file: {json_to_fill}. Be aware of typing errors of the user. If you don't find the information to fill a slot, leave it as null. Print ONLY this JSON file: {json_to_fill}, but with the nulls filled with the information you got, and NOTHING ELSE after."""
    filled_json: str = utils.askAndReadAnswer(process, instruction)
    filled_json_list : list[dict] = utils.stringToJson(filled_json)
    other_request: str = utils.llmSupervision(dialogueST)
    dialogueST.update_intentions(filled_json_list)
    if DEBUG or DEBUG_LLM:
        print("Filled JSON received in fillWithCurrentInfo: ", json.dumps(filled_json_list, indent=2))
    return other_request
    
    


# If there are intentions with no null slots, we fulfill them directly
def fulfillIntent(dialogueST: DialogueStateTracker, list_db: ListDatabase) -> tuple[str, list[str], str]:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in fulfillIntent.")
    ret_val: str = ""
    actions_performed: str = "" # A written report of what action the LLM has completed
    other_request: str = "" # This is needed ONLY to create the answer for the fallback policy
    no_movie: list[str] = [] # In case of no movie/series found for information request or for list add
    other_request = utils.llmSupervision(dialogueST)
    for intention in dialogueST.get_intentions_json(): 
        if None not in intention.values() and intention.get("fulfilled") == False:
            ret_val = actions.execute(intention, list_db, dialogueST)
            if ret_val == intention.get("object_title"): # no action was performed for movie info or adding movie to list because no movie found
                if DEBUG or DEBUG_LLM:
                    print("No action was performed for the given intention:", intention)
                no_movie.append(ret_val)
            elif intention.get("intent") == OTHER_INTENT:
                # Simply return the text of the other request for later use in fallback policy
                other_request = other_request + "; " + ret_val
                intention["fulfilled"] = True
            else:
                actions_performed = actions_performed + ret_val # do the correspondent action for each intention, like printing a list or call an API for movie info ecc.
                intention["fulfilled"] = True
    if DEBUG or DEBUG_LLM:
        print("Actions performed in fulfillIntent: ", actions_performed)
        print("Intentions after fulfilling in fulfillIntent: ", json.dumps(dialogueST.get_intentions_json(), indent=2))
    # Remove the fulfilled intentions from the list
    unfulfilled_intentions: list[dict] = [intent for intent in dialogueST.get_intentions_json() if intent.get("fulfilled") == False]
    # Change the values of movie title not found to None
    for intention in unfulfilled_intentions:
        if intention.get("intent") == MOVIE_INFORMATION_REQUEST_INTENT or intention.get("intent") == MODIFY_EXISTING_LIST_INTENT:
            if intention.get("object_title") in no_movie:
                intention.update({"object_title": None})
    dialogueST.update_intentions(unfulfilled_intentions)
    if DEBUG or DEBUG_LLM:
        print("Unfulfilled intentions after cleaning in fulfillIntent: ", unfulfilled_intentions)
    return actions_performed, no_movie, other_request


def fillNullSlots(dialogueST: DialogueStateTracker, process: subprocess.Popen, no_movie: list[str], other_request: str) -> str | None:

    if DEBUG or DEBUG_LLM:
        print("DEBUG in fillNullSlots.")
    # Check if there are still null slots 
    if (any(None in intention.values() for intention in dialogueST.get_intentions_json())):
        userResponse: str = ""
        userResponse = askUser(process, dialogueST, no_movie, other_request)
        if DEBUG or DEBUG_LLM:
            print("User response received in fillNullSlots: ", userResponse)
        # Now the user answer is part of our current info
        fillWithCurrentInfo(process, dialogueST)
        if DEBUG or DEBUG_LLM:
            print("Filled JSON after asking user in fillNullSlots: ", json.dumps(dialogueST.get_intentions_json(), indent=2))
        return userResponse
    else:
        print("All null slots have been filled.")
        return None

def askUser(process: subprocess.Popen, dialogueST: DialogueStateTracker, no_movie: list[str], other_request: str) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in askUser")
    instruction: str = ""
    # We generate the question for the user for more information. Inside the question there is also the 
    # communication of previously performed actions or failure to fulfill something out of boundaries
    instruction= nlg.generateLLMResponse(dialogueST, no_movie, other_request)
    llmAnswer: str = utils.askAndReadAnswer(process, instruction) # the LLM actually asks the user something. It also communicate any action performed so far and any fallback policy (if the user requested something outside the boundaries of the system)
    # If the user had an other intent, we already answered him that we can't handle it, 
    # so we fulfilled it. We mark it as fulfilled so we don't ask again later
    for intention in dialogueST.get_intentions_json(): #it's for safety, should be already fulfilled
        if intention.get("intent") == OTHER_INTENT:
            intention["fulfilled"] = True
    dialogueST.add_turn("Movie Assistant: " + llmAnswer)
    if DEBUG or DEBUG_LLM:
        print("LLM asks the user:", llmAnswer)
    userInput: str = input("User: ")
    dialogueST.update_last_user_input(userInput)
    dialogueST.add_turn("User: " + userInput)
    return userInput