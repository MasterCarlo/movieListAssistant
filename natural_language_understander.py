import subprocess
import time
import os
import json
import re

from global_variables import *
import dialogue_manager
from dialogue_state_tracker import DialogueStateTracker

# # we check the intention of the user
# if OTHER_INTENT in dialogue_state_tracker.dialogueST.get_json():
#     if INFO_REQUEST_INTENT in dialogue_state_tracker.dialogueST.get_json() or MODIFY_LIST_INTENT in dialogue_state_tracker.dialogueST.get_json():
#         #the user expressed at least one legitimate intention and a non legitimate one
#         system_prompt = "You are a movie expert. A user asked something "


# We check the intentions of the user inside the json from the dialogue state tracker. 
# Then we return a corresponding json for each intention to complete 
def extractIntentions(jsonAnswer: str) -> list[str]:
    
    intentions: str = jsonAnswer
    intentions_list_json: list[dict] = []
    if "create new list" in intentions:
        intent: dict = json.loads("""{"intent": "create new list", "list_name": null, "fulfilled": false}""")
        intentions_list_json.append(intent)
    if "modify existing list" in intentions:
        intent: dict = json.loads("""{"intent": "modify existing list", "list_name": null, "action": null, "object_title": null, "fulfilled": false}""")
        intentions_list_json.append(intent)
    if "movie information request" in intentions:
        intent: dict = json.loads("""{"intent": "movie information request", "object_of_the_information": null, "text_of_the_request": null, "fulfilled": false}""")
        intentions_list_json.append(intent)
    if "other" in intentions:
        intent: dict = json.loads("""{"intent": "other", "text_of_the_request": null, "fulfilled": false}""")
        intentions_list_json.append(intent)
    
    return intentions_list_json


def checkForIntention(dialogueST: DialogueStateTracker, userResponse: str) -> bool:
    pass