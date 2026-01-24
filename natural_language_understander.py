import subprocess
import time
import os
import json
import re
import utils
import subprocess

from global_variables import *
from dialogue_state_tracker import DialogueStateTracker


# TODO: testare col debug le funzioni modify list e get movie information

# We check the intentions of the user inside the json from the dialogue state tracker. 
# Then we return a corresponding json for each intention to complete 
def extractIntentions(json_answer: str) -> list[dict]:
    if DEBUG or DEBUG_LLM:
        print("DEBUG in extractIntentions")
        print("JSON answer to extract intentions from:", json_answer)
    if len(json_answer) > 3: # if it's not an empty json list "[]"
        intentions: list[dict] = json.loads(json_answer)
        intentions_list_json: list[dict] = []
        for intention in intentions:
            if CREATE_NEW_LIST_INTENT in intention.values():
                intent: dict = json.loads("""{"intent":""" + """\"""" + CREATE_NEW_LIST_INTENT + """\", "list_name": null, "fulfilled": false}""")
                intentions_list_json.append(intent)
            elif MODIFY_EXISTING_LIST_INTENT in intention.values():
                intent: dict = json.loads("""{"intent":""" + """\"""" + MODIFY_EXISTING_LIST_INTENT + """\", "list_name": null, "action": [null], "object_title": null, "fulfilled": false}""")
                intentions_list_json.append(intent)
            elif SHOW_EXISTING_LIST_INTENT in intention.values():
                intent: dict = json.loads("""{"intent":""" + """\"""" + SHOW_EXISTING_LIST_INTENT + """\", "list_name": null, "fulfilled": false}""")
                intentions_list_json.append(intent)
            elif MOVIE_INFORMATION_REQUEST_INTENT in intention.values():
                intent: dict = json.loads("""{"intent":""" + """\"""" + MOVIE_INFORMATION_REQUEST_INTENT + """\", "object_title": null, "information_requested": [null], "fulfilled": false}""")
                intentions_list_json.append(intent)
            elif CANCEL_REQUEST_INTENT in intention.values():
                intent: dict = json.loads("""{"intent":""" + """\"""" + CANCEL_REQUEST_INTENT + """\", "intent_to_cancel": null, "fulfilled": false}""")
                intentions_list_json.append(intent)
            elif OTHER_INTENT in intention.values():
                intent: dict = json.loads("""{"intent":""" + """\"""" + OTHER_INTENT + """\", "text_of_the_request": null, "fulfilled": false}""")
                intentions_list_json.append(intent)
        
        return intentions_list_json
    else:
        if DEBUG or DEBUG_LLM:
            print("No intentions found in the JSON answer.")
        return []


def checkForIntention(process: subprocess.Popen, dialogueST: DialogueStateTracker):
    if DEBUG or DEBUG_LLM:
        print("DEBUG in nlu.checkForIntention")
    user_response: str = dialogueST.get_last_user_input()
    string: str = f"I want you to extract the intentions of the user from this user input (the last: {user_response})."
    string2: str = ""
    if dialogueST.get_intentions_json() != []:
        string: str = f"""This is the JSON with the previously expressed intentions of the user: {utils.jsonToString(dialogueST.get_intentions_json())}. I want you to extract, from this user input (the last: {user_response}), any NEW intention that is not already present in that json."""
        string2: str = f"The user can have the same intention as before but with a different data (for example asking about movie information as before, but for a different movie), if so, consider it a new intention"
    last_N_turns: str = " ".join(dialogueST.get_last_N_turns())
    instruction: str = f"""You are a movie list assistant. This is the content of your previous conversation with the user: "{last_N_turns}". {string}. They can be: [{CREATE_NEW_LIST_INTENT}], [{MODIFY_EXISTING_LIST_INTENT}], [{SHOW_EXISTING_LIST_INTENT}], [{MOVIE_INFORMATION_REQUEST_INTENT}], [{CANCEL_REQUEST_INTENT}], [{OTHER_INTENT}]. Every intent that is not in this list, MUST to be classified as [{OTHER_INTENT}]. {string2}. The [{CANCEL_REQUEST_INTENT}] intention is hard to catch, it's rarely explicit: if the user say something like "never mind", "I don't care anymore", "go on", "don't worry" etc., probably he wants to cancel his previous request. For the {MODIFY_EXISTING_LIST_INTENT}, these are the only actions possible: [{", ".join(MODIFY_LIST_ACTIONS)}]. If the action is even slightly different from these ones, the intent has to be considered [{OTHER_INTENT}]. For the {MOVIE_INFORMATION_REQUEST_INTENT}, these are the only info requests possible: [{", ".join(MOVIE_INFO_ACTIONS)}]. If the user wants to know anything else, like the title of a movie, the country etc., you have to consider the intent as {OTHER_INTENT}. If and only if there are new intentions, print ONLY a json file with ONLY the new intentions and nothing else; otherwise print an empty json list. For example: [{{"intention": "{MOVIE_INFORMATION_REQUEST_INTENT}"}}, {{"intention": " {MODIFY_EXISTING_LIST_INTENT}"}}, {{"intention":"{MODIFY_EXISTING_LIST_INTENT}"}}]."""
    json_intentions: str = utils.askAndReadAnswer(process, instruction)
    if DEBUG or DEBUG_LLM:
        print("New intentions JSON Answer received in checkForIntentions: ", json_intentions)
    if json_intentions != "[]":
        new_intentions_json: list[dict] = extractIntentions(json_intentions)
        old_intentions: list[dict] = dialogueST.get_intentions_json()
        old_intentions.extend(new_intentions_json)
        dialogueST.update_intentions(old_intentions) # its confusing that i update with old intentions and not new intentions, TODO: change that
        if DEBUG or DEBUG_LLM:
            print("Updated intentions in dialogue state tracker in checkForIntention:", json.dumps(dialogueST.get_intentions_json(), indent=2))
    elif DEBUG or DEBUG_LLM:
        print("No new intentions found in checkForIntention.")