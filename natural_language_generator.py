import json

from global_variables import *
from dialogue_state_tracker import DialogueStateTracker

# We generate a question to ask the user to fill the null slots in the json intentions.
# json_to_fill is the json with the intentions filled as much as possible with previous information, 
# but it still has null slots
def generateLLMResponse(dialogueST: DialogueStateTracker, other_request: str) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in nlg.generateLLMResponse.")
    other: list[str] = []
    actions_performed: str = ""
    if dialogueST.get_actions_performed() != "":
        actions_performed = "These are the actions executed by you so far, on user request: " + dialogueST.get_actions_performed() + ". Inform the user that these actions have been performed."
    json_to_fill: str = json.dumps(dialogueST.get_intentions_json())
    last_N_turns: list[str] = dialogueST.get_last_N_turns()
    last_N_turns: str = "  ".join(last_N_turns)
    instruction: str = "You are a movie list assistant and movie expert, you can help the user only " + MODIFY_EXISTING_LIST_INTENT + ", " + CREATE_NEW_LIST_INTENT + " or answering to his " + MOVIE_INFORMATION_REQUEST_INTENT + ". " + actions_performed
    for intention in dialogueST.get_intentions_json():
        if CREATE_NEW_LIST_INTENT in intention.keys():
            if None in intention.values():
                # ask for the name of the new list
                instruction= instruction + "The user wants to create a new movie list but hasn't specified the name of the list. Please ask the user for the name of the new list or suggest a name for the list based on the previous conversation if possible."
        elif MODIFY_EXISTING_LIST_INTENT in intention.keys():
            if None in intention.values():
                # ask for the name of the list to modify, the action and the object title
                instruction= instruction + f"The user wants to modify an existing movie list but hasn't specified the name of the list, the action to perform (only actions possible: {MODIFY_LIST_ACTIONS}) and/or the title of the object (a movie or a series or the new name of a list). Please ask the user for these details or suggest them based on the previous conversation if possible."
        elif MOVIE_INFORMATION_REQUEST_INTENT in intention.keys():
            if None in intention.values():
                # ask for the object of the information and the text of the request
                instruction= instruction + f"The user has requested movie or series information but hasn't specified the object of the information (a movie or a series) and/or the specific information requested (possible options: {MOVIE_INFO_ACTIONS}). Please ask the user for these details or suggest them based on the previous conversation if possible."
        elif SHOW_EXISTING_LIST_INTENT in intention.keys():
            if None in intention.values():
                # ask for the name of the list to show
                instruction= instruction + "The user wants to see an existing movie list but hasn't specified the name of the list. Please ask the user for the name of the list or suggest a name for the list based on the previous conversation if possible."
        elif OTHER_INTENT in intention.keys(): 
            # we can't manage this intent
            if not None in intention.values():
                request: str = intention.get("request")
                other.append(request)
            else:
                print("The other intent text of the request is empty.")
    
    fallback_policy: str = FALLBACK_POLICY + "This is the text of the request(s): "
    if len(other) > 0:
        fallback_policy = fallback_policy + "; ".join(other)
    # other request is "" or something so no problem in adding it
    instruction = instruction + fallback_policy + other_request + "This is the content of your previous conversation with the user: \"" + last_N_turns + "\".  This is the json file you are trying to fill: " + json_to_fill + " . Print only what you want to say to the user, like you are talking to him directly, and NOTHING else."
    return instruction

def communicateCompletion(dialogueST: DialogueStateTracker, other_request: str) -> str:
    
    if DEBUG:
        print("DEBUG in communicateCompletion")
    if dialogueST.get_actions_performed() != "":
        if other_request != "":
            fallback_policy: str = FALLBACK_POLICY + "This is the text of the request(s): " + other_request
        instruction: str = "You are a movie list assistant and movie expert, you helped the user with all his requests. These are the actions you have completed: " + dialogueST.get_actions_performed() + ". This is your previous conversation with the user: \"" + dialogueST.get_last_N_turns() + "\". Please, inform the user that all his requests have been satisfied." + fallback_policy + ". Ask the user if he needs further assistance."
    else:
        print("There is some problem in communicateCompletion")
        return ""
    return instruction