import subprocess
import json
import utils
import natural_language_generator as nlg

from global_variables import *
from dialogue_state_tracker import DialogueStateTracker
from natural_language_generator import Unsuccess
from list_database import ListDatabase


# We fill the null slots in the intentions json using the conversation history 
def fillWithCurrentInfo(process: subprocess.Popen, dialogueST: DialogueStateTracker, list_db: ListDatabase) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in nlu.fillWithCurrentInfo.")
        print("Current intentions JSON to fill:", json.dumps(dialogueST.get_intentions_json(), indent=2))
    # Get the last N turns of the conversation from the dialogue state tracker
    last_N_turns: str = "  ".join(dialogueST.get_last_N_turns())
    json_to_fill: str = utils.jsonToString(dialogueST.get_intentions_json()) # We need one line json because shell can't manage multi line text
    existing_lists: str = ""
    if list_db.get_all_lists() != {}:
        existing_lists = ALL_LISTS + list_db.get_all_lists().keys().__str__() + "."
    instruction: str = f"""You are a movie list assistant, you can help the user only {MODIFY_EXISTING_LIST_INTENT}, {CREATE_NEW_LIST_INTENT}, {CANCEL_REQUEST_INTENT} or answering to his {MOVIE_INFORMATION_REQUEST_INTENT}. If the user asks something else, his intent must be classified as [{OTHER_INTENT}]. The [{CANCEL_REQUEST_INTENT}] intention is hard to catch, it's rarely explicit: if the user say something like "never mind", "I don't care anymore", "go on", "don't worry" etc., probably he wants to cancel his previous request. For the {MODIFY_EXISTING_LIST_INTENT}, these are the only action possible: [{', '.join(MODIFY_LIST_ACTIONS)}]. If the action is even slightly different from these ones, the intent has to be considered [{OTHER_INTENT}]. For the {MOVIE_INFORMATION_REQUEST_INTENT}, these are the only info requests possible: [{', '.join(MOVIE_INFO_ACTIONS)}]. If the info request is even slightly different from these ones, the intent has to be considered {OTHER_INTENT}. {existing_lists}. This is the content of your previous conversation with the user:" {last_N_turns}". Use the content of that conversation to fill the null slots inside this json file: {json_to_fill}. Be aware of typing errors of the user. If you think that some filled slots were filled incorrectly, feel free to fill them with the correct value, but be careful. If you don't find the information to fill a slot, leave it as null. Print ONLY this JSON file: {json_to_fill}, but with the null slots filled with the information you got and, if necessary, with the changed values for corrections, and NOTHING ELSE after."""
    filled_json: str = utils.askAndReadAnswer(process, instruction)
    filled_json_list: list[dict] = utils.stringToJson(filled_json)
    dialogueST.update_intentions(filled_json_list)
    unsuccess: Unsuccess = utils.llmSupervision(dialogueST)
    if DEBUG or DEBUG_LLM:
        print("Filled JSON received in fillWithCurrentInfo: ", json.dumps(filled_json_list, indent=2))
    return unsuccess


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


def checkForIntention(process: subprocess.Popen, dialogueST: DialogueStateTracker, list_db: ListDatabase):
    if DEBUG or DEBUG_LLM:
        print("DEBUG in nlu.checkForIntention")
    user_response: str = dialogueST.get_last_user_input()
    string: str = f"I want you to extract the intentions of the user from this user input (the last: {user_response})."
    string2: str = ""
    if dialogueST.get_intentions_json() != []:
        string: str = f"""This is the JSON with the previously expressed intentions of the user: {utils.jsonToString(dialogueST.get_intentions_json())}. I want you to extract, from this user input (the last: {user_response}), any NEW intention that is not already present in that json."""
        string2: str = f"The user can have the same intention as before but with a different data (for example asking about movie information as before, but for a different movie), if so, consider it a new intention"
    existing_lists: str = ""
    if list_db.get_all_lists() != {}:
        existing_lists = ALL_LISTS + list_db.get_all_lists().keys().__str__() + "."
    last_N_turns: str = " ".join(dialogueST.get_last_N_turns())
    instruction: str = f"""You are a movie list assistant. This is the content of your previous conversation with the user: "{last_N_turns}". {string}. They can be: [{CREATE_NEW_LIST_INTENT}], [{MODIFY_EXISTING_LIST_INTENT}], [{SHOW_EXISTING_LIST_INTENT}], [{MOVIE_INFORMATION_REQUEST_INTENT}], [{CANCEL_REQUEST_INTENT}], [{OTHER_INTENT}]. Every intent that is not in this list, MUST to be classified as [{OTHER_INTENT}]. {string2}. {existing_lists}. The [{CANCEL_REQUEST_INTENT}] intention is hard to catch, it's rarely explicit: if the user say something like "never mind", "I don't care anymore", "go on", "don't worry" etc., probably he wants to cancel his previous request. For the {MODIFY_EXISTING_LIST_INTENT}, these are the only actions possible: [{", ".join(MODIFY_LIST_ACTIONS)}]. If the action is even slightly different from these ones, the intent has to be considered [{OTHER_INTENT}]. For the {MOVIE_INFORMATION_REQUEST_INTENT}, these are the only info requests possible: [{", ".join(MOVIE_INFO_ACTIONS)}]. If the user wants to know anything else, like the title of a movie, the country etc., you have to consider the intent as {OTHER_INTENT}. If and only if there are new intentions, print ONLY a json file with ONLY the new intentions and nothing else; otherwise print an empty json list. For example: [{{"intention": "{MOVIE_INFORMATION_REQUEST_INTENT}"}}, {{"intention": " {MODIFY_EXISTING_LIST_INTENT}"}}, {{"intention":"{MODIFY_EXISTING_LIST_INTENT}"}}]."""
    json_intentions: str = utils.askAndReadAnswer(process, instruction)
    if DEBUG or DEBUG_LLM:
        print("New intentions JSON Answer received in checkForIntentions: ", json_intentions)
    if json_intentions != "[]":
        new_intentions_json: list[dict] = extractIntentions(json_intentions)
        old_intentions: list[dict] = dialogueST.get_intentions_json()
        old_intentions.extend(new_intentions_json)
        dialogueST.update_intentions(old_intentions) # its confusing that i update with old intentions and not new intentions
        if DEBUG or DEBUG_LLM:
            print("Updated intentions in dialogue state tracker in checkForIntention:", json.dumps(dialogueST.get_intentions_json(), indent=2))
    elif DEBUG or DEBUG_LLM:
        print("No new intentions found in checkForIntention.")