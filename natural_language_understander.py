import subprocess
import time
import os
import json
import re
import utils
import subprocess

from global_variables import *
from dialogue_state_tracker import DialogueStateTracker

# # we check the intention of the user
# if OTHER_INTENT in dialogue_state_tracker.dialogueST.get_json():
#     if INFO_REQUEST_INTENT in dialogue_state_tracker.dialogueST.get_json() or MODIFY_LIST_INTENT in dialogue_state_tracker.dialogueST.get_json():
#         #the user expressed at least one legitimate intention and a non legitimate one
#         system_prompt = "You are a movie expert. A user asked something "

# TODO: testare col debug le funzioni modify list e get movie information

# We check the intentions of the user inside the json from the dialogue state tracker. 
# Then we return a corresponding json for each intention to complete 
def extractIntentions(json_answer: str) -> list[dict]:
    if DEBUG:
        print("Debug mode in extractIntentions")
        print("JSON answer to extract intentions from:", json_answer)
    if len(json_answer) > 3: # if it's not an empty json list "[]"
        intentions: str = json_answer
        intentions_list_json: list[dict] = []
        if CREATE_NEW_LIST_INTENT in intentions:
            intent: dict = json.loads("""{"intent":""" + """\"""" + CREATE_NEW_LIST_INTENT + """\", "list_name": null, "fulfilled": false}""")
            intentions_list_json.append(intent)
        if MODIFY_EXISTING_LIST_INTENT in intentions:
            intent: dict = json.loads("""{"intent":""" + """\"""" + MODIFY_EXISTING_LIST_INTENT + """\", "list_name": null, "action": [null], "object_title": null, "fulfilled": false}""")
            intentions_list_json.append(intent)
        if SHOW_EXISTING_LIST_INTENT in intentions:
            intent: dict = json.loads("""{"intent":""" + """\"""" + SHOW_EXISTING_LIST_INTENT + """\", "list_name": null, "fulfilled": false}""")
            intentions_list_json.append(intent)
        if MOVIE_INFORMATION_REQUEST_INTENT in intentions:
            intent: dict = json.loads("""{"intent":""" + """\"""" + MOVIE_INFORMATION_REQUEST_INTENT + """\", "object_title": null, "information_requested": [null], "fulfilled": false}""")
            intentions_list_json.append(intent)
        if CANCEL_REQUEST_INTENT in intentions:
            intent: dict = json.loads("""{"intent":""" + """\"""" + CANCEL_REQUEST_INTENT + """\", "request": null, "fulfilled": false}""")
            intentions_list_json.append(intent)
        if OTHER_INTENT in intentions:
            intent: dict = json.loads("""{"intent":""" + """\"""" + OTHER_INTENT + """\", "text_of_the_request": null, "fulfilled": false}""")
            intentions_list_json.append(intent)
        
        return intentions_list_json
    else:
        print("No intentions found in the JSON answer.")
        return []


def checkForIntention(process: subprocess.Popen, dialogueST: DialogueStateTracker):
    user_response: str = dialogueST.get_last_user_input()
    intentions_str: str = json.dumps(dialogueST.get_intentions_json())
    last_N_turns: str = " ".join(dialogueST.get_last_N_turns())
    instruction: str = f"""You are a movie list assistant and movie expert, you can help the user only {MODIFY_EXISTING_LIST_INTENT}, {CREATE_NEW_LIST_INTENT}, {SHOW_EXISTING_LIST_INTENT}, answer his {MOVIE_INFORMATION_REQUEST_INTENT} or {CANCEL_REQUEST_INTENT}. This is the content of your previous conversation with the user: {last_N_turns}. Given the current intentions of the user expressed in this json: {intentions_str}, I want you to extract, from the last user input ({user_response}), any NEW intention that is not already present in the json, they can be: [{CREATE_NEW_LIST_INTENT}], [{MODIFY_EXISTING_LIST_INTENT}], [{SHOW_EXISTING_LIST_INTENT}], [{MOVIE_INFORMATION_REQUEST_INTENT}], [{CANCEL_REQUEST_INTENT}], [{OTHER_INTENT}]. The user can have the same intention as before but with a different data (for example asking about movie information as before, but for a different movie), if so, consider it a new intention. If and only if there are new intentions, print ONLY a json file with ONLY the new intentions and nothing else, for example For example: [{{"intention": "{MOVIE_INFORMATION_REQUEST_INTENT}"}}, {{"intention": " {MODIFY_EXISTING_LIST_INTENT}"}}, {{"intention":"{MODIFY_EXISTING_LIST_INTENT}"}}]. Otherwise print an empty json list: []."""
    json_intentions: str = utils.askAndReadAnswer(process, instruction)
    print("New intentions JSON Answer received: ", json_intentions)
    new_intentions_list_json: list[dict] = extractIntentions(json_intentions)
    if len(new_intentions_list_json) > 0:
        list_of_inte: list[dict] = dialogueST.get_intentions_json()
        list_of_inte.extend(new_intentions_list_json)
        dialogueST.update_intentions(list_of_inte)
        if DEBUG or DEBUG_LLM:
            print("Updated intentions in dialogue state tracker in checkForIntention:", dialogueST.get_intentions_json())
    elif DEBUG or DEBUG_LLM:
        print("No new intentions found in checkForIntention.")
    