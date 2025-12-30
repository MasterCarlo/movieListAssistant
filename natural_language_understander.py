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
    intentions_list_json: list[str] = []
    if "create new list" in intentions:
        intentions_list_json.append("""{"intent": "create new list", "list_name": null}""")
    if "modify existing list" in intentions:
        intentions_list_json.append("""{"intent": "modify existing list", "list_name": null, "action": null, "object_title": null}""")
    if "movie information request" in intentions:
        intentions_list_json.append("""{"intent": "movie information request", "object_of_the_information": null, "text_of_the_request": null}""")
    if "other" in intentions:
        intentions_list_json.append("""{"intent": "other", "text_of_the_request": null}""")
    
    return intentions_list_json
    