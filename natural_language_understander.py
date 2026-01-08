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


# We check the intentions of the user inside the json from the dialogue state tracker. 
# Then we return a corresponding json for each intention to complete 
def extractIntentions(json_answer: str) -> list[str]:
    if len(json_answer) > 3: # if it's not an empty json list "[]"
        intentions: str = json_answer
        intentions_list_json: list[dict] = []
        if CREATE_NEW_LIST_INTENT in intentions:
            intent: dict = json.loads("""{"intent": "create new list", "list_name": null, "fulfilled": false}""")
            intentions_list_json.append(intent)
        if MODIFY_EXISTING_LIST_INTENT in intentions:
            intent: dict = json.loads("""{"intent": "modify existing list", "list_name": null, "action": null, "object_title": null, "fulfilled": false}""")
            intentions_list_json.append(intent)
        if SHOW_EXISTING_LIST_INTENT in intentions:
            intent: dict = json.loads("""{"intent": "show existing list", "list_name": null, "fulfilled": false}""")
            intentions_list_json.append(intent)
        if MOVIE_INFORMATION_REQUEST_INTENT in intentions:
            intent: dict = json.loads("""{"intent": "movie information request", "object_of_the_information": null, "text_of_the_request": null, "fulfilled": false}""")
            intentions_list_json.append(intent)
        if OTHER_INTENT in intentions:
            intent: dict = json.loads("""{"intent": "other", "text_of_the_request": null, "fulfilled": false}""")
            intentions_list_json.append(intent)
        
        return intentions_list_json
    else:
        print("No intentions found in the JSON answer.")
        return []


def checkForIntention(process: subprocess.Popen, dialogueST: DialogueStateTracker):
    user_response: str = dialogueST.get_last_user_input()
    intentions_str: str = json.dumps(dialogueST.get_intentions_json())
    last_N_turns: str = "  ".join(dialogueST.get_last_N_turns())
    instruction: str = f"""You are a movie list assistant and movie expert, you can help the user only modifying an existing list, creating a new list or answering to his movie information requests. This is the content of your previous conversation with the user: {last_N_turns}. You can extract the intentions from the user input, they can be [create new list], [modify existing list], [show existing list], [movie information request], [other]. Given the current intentions of the user expressed in this json: {intentions_str}, I want you to extract, from the last user input ({user_response}), any NEW intention that is not already present in the json. The user can have the same intention as before but with a different data (for example asking about movie information as before, but for a different movie), if so, consider it a new intention and print it in the json list. If there are new intentions, print ONLY a json list with ONLY the new intentions and nothing else, otherwise print an empty json list: []."""
    json_intentions: str = utils.askAndReadAnswer(process, instruction)
    print("New intentions JSON Answer received: ", json_intentions)
    new_intentions_list_json: list[dict] = extractIntentions(json_intentions)
    list_of_int: list[dict] = dialogueST.get_intentions_json()
    if len(new_intentions_list_json) > 0:
        list_of_int.extend(new_intentions_list_json)
        dialogueST.update_intentions_json(list_of_int)
    