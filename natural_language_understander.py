import subprocess
import time
import os
import json
import re

from global_variables import *
import dialogue_manager
import dialogue_state_tracker

# we check the intention of the user
if OTHER_INTENT in dialogue_state_tracker.dialogueST.get_json():
    if INFO_REQUEST_INTENT in dialogue_state_tracker.dialogueST.get_json() or MODIFY_LIST_INTENT in dialogue_state_tracker.dialogueST.get_json():
        #the user expressed at least one legitimate intention and a non legitimate one
        system_prompt = "You are a movie expert. A user asked something "


# we check the intentions of the user inside the json from the dialogue state tracker and we return the corresponding json to complete
def extractIntentionsJson(dialogueST):

    intentions_json = dialogueST.get_intentions_json()
    json_list = []
    if "create new list" in intentions_json:
        json_list.append("""{"intent": "create new list", list name": null}""")
    if "modify existing list" in intentions_json:
        json_list.append("""{"intent": "modify existing list", list name": null, "action": null, "object_title": null}""")
    if "information request" in intentions_json:
        json_list.append("""{"intent": "information request", "object of the information": null, "text of the request": null}""")
    if "other" in intentions_json:
        json_list.append("""{"intent": "other"}""")
    
    return json_list
    