# The dialogue manager chooses the next best action 

import json
import subprocess
import utils
import actions
import natural_language_generator as nlg
import natural_language_understander as nlu

from list_database import ListDatabase
from dialogue_state_tracker import DialogueStateTracker
from natural_language_generator import Unsuccess
from global_variables import *


# We respond to the user. First we understand if we can fill the nulls with the current information or if we need more information
# (that we will ask to the the user), then, based on the last user input we generate an appropriate response
def followupInteraction(dialogueST: DialogueStateTracker, list_db: ListDatabase, process: subprocess.Popen):

    if DEBUG or DEBUG_LLM:
        print("JSON intentions in followupInteraction")
    # First we fill the intentions json with our current info
    unsuccess: Unsuccess = nlu.fillWithCurrentInfo(process, dialogueST, list_db)
    # We check if there are intentions with no null slots that we can fulfill directly. We register the actions performed
    actions_performed: str = ""
    uns: Unsuccess = Unsuccess()
    actions_performed, uns = fulfillIntent(dialogueST, list_db, unsuccess)
    unsuccess.merge(uns)
    dialogueST.update_actions(actions_performed) # update the actions performed so far
    
    # Now we check if there are still intentions to fulfill, it means the intention_json is uncomplete (it has null slots)
    if(any(False in intention.values() for intention in dialogueST.get_intentions_json())): 
        # If there are null slots in the json, we need to fill them
        if(any(None in intention.values() for intention in dialogueST.get_intentions_json())): # we search for None instead of null because of python json format
            if DEBUG or DEBUG_LLM:
                print("There are null slots to fill, we will ask the LLM to fill them.")
            user_response: str | None = fillNullSlots(dialogueST, process, unsuccess, list_db)
            result: tuple[str, Unsuccess] = fulfillIntent(dialogueST, list_db, unsuccess)
            actions_performed = actions_performed + result[0]
            dialogueST.update_actions(actions_performed)
            # After filling the null slots, we check if there are new intentions from the user response.
            # If present, in the next interaction we will take care of them
            if user_response:
                nlu.checkForIntention(process, dialogueST, list_db)
        else:
            if DEBUG or DEBUG_LLM:
                print("No null slots to fill")
    else: # All intentions have been fulfilled
        if DEBUG or DEBUG_LLM:
            print("All intentions have been fulfilled.")
        instruction: str = nlg.completion(dialogueST, unsuccess) # we communicate the user the completion of all his requests and the unsuccessful outcomes if any
        llmAnswer: str = utils.askAndReadAnswer(process, instruction) # we tell the LLM to inform the user that all his requests have been satisfied
        print("Movie Assistant:", llmAnswer)
        dialogueST.add_turn("Movie Assistant: " + llmAnswer)
        user_response: str = input("User: ")
        dialogueST.update_last_user_input(user_response)
        dialogueST.add_turn("User: " + user_response)
        nlu.checkForIntention(process, dialogueST, list_db)


# If there are intentions with no null slots, we fulfill them directly
def fulfillIntent(dialogueST: DialogueStateTracker, list_db: ListDatabase, unsuccess: Unsuccess) -> tuple[str, Unsuccess]:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in fulfillIntent.")
        print("Intentions before fulfilling in fulfillIntent: ", json.dumps(dialogueST.get_intentions_json(), indent=2))
    actions_performed: str = "" # A written report of what action the LLM has completed
    intent_order = [CANCEL_REQUEST_INTENT, CREATE_NEW_LIST_INTENT, MODIFY_EXISTING_LIST_INTENT,
                    SHOW_EXISTING_LIST_INTENT, MOVIE_INFORMATION_REQUEST_INTENT, OTHER_INTENT]
    order_index = {intent: i for i, intent in enumerate(intent_order)}
    sorted_intentions: list[dict] = sorted(dialogueST.get_intentions_json(), key=lambda x: order_index.get(x.get("intent"), len(intent_order)))
    dialogueST.update_intentions(sorted_intentions)
    for intention in dialogueST.get_intentions_json(): 
        if None not in intention.values() and intention.get("fulfilled") == False:
            outcome: str | Unsuccess = actions.execute(intention, list_db, dialogueST)
            if isinstance(outcome, Unsuccess):
                if DEBUG or DEBUG_LLM:
                    print("No action was performed for the given intention:", intention)
                unsuccess.merge(outcome)
            else: # if outcome is a string
                actions_performed = actions_performed + outcome # the correspondent actions for each intention, like printing a list or call an API for movie info ecc.
    if DEBUG or DEBUG_LLM:
        print("Intentions after fulfilling in fulfillIntent: ", json.dumps(dialogueST.get_intentions_json(), indent=2))
    # Remove the fulfilled intentions from the list
    unfulfilled_intentions: list[dict] = [intent for intent in dialogueST.get_intentions_json() if intent.get("fulfilled") == False]
    if DEBUG or DEBUG_LLM:
        print("Intentions before cleaning in fulfillIntent: ", json.dumps(dialogueST.get_intentions_json(), indent=2))
        print("Actions performed in fulfillIntent: ", actions_performed)
        print("Unfulfilled intentions after cleaning in fulfillIntent: ", unfulfilled_intentions)
    dialogueST.update_intentions(unfulfilled_intentions)
    return actions_performed, unsuccess

def fillNullSlots(dialogueST: DialogueStateTracker, process: subprocess.Popen, unsuccess: Unsuccess, list_db: ListDatabase) -> str | None:

    if DEBUG or DEBUG_LLM:
        print("DEBUG in fillNullSlots.")
    # Check if there are still null slots 
    if (any(None in intention.values() for intention in dialogueST.get_intentions_json())):
        userResponse: str = ""
        userResponse = nlg.askUser(process, dialogueST, unsuccess, list_db)
        if DEBUG or DEBUG_LLM:
            print("User response received in fillNullSlots: ", userResponse)
        # Now the user answer is part of our current info
        nlu.fillWithCurrentInfo(process, dialogueST, list_db)
        if DEBUG or DEBUG_LLM:
            print("Filled JSON after asking user in fillNullSlots: ", json.dumps(dialogueST.get_intentions_json(), indent=2))
        return userResponse
    else:
        if DEBUG or DEBUG_LLM:
            print("All null slots have been filled.")
        return None