import utils

from global_variables import *
from dialogue_state_tracker import DialogueStateTracker
from utils import Unsuccess

# We generate a question to ask the user to fill the null slots in the json intentions.
# json_to_fill is the json with the intentions filled as much as possible with previous information, 
# but it still has null slots
def generateLLMResponse(dialogueST: DialogueStateTracker, unsuccess: Unsuccess) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in nlg.generateLLMResponse.")
    other: list[str] = []
    actions_performed: str = ""
    if dialogueST.get_actions_performed() != "":
        actions_performed = "These are the actions executed by you so far, on user request: " + dialogueST.get_actions_performed() + ". Inform the user that these actions have been performed."
    json_to_fill: str = utils.jsonToString(dialogueST.get_intentions_json())
    last_N_turns: str = " ".join(dialogueST.get_last_N_turns())
    instruction: str = "You are a movie list assistant, you can help the user only " + MODIFY_EXISTING_LIST_INTENT + ", " + CREATE_NEW_LIST_INTENT + ", " + CANCEL_REQUEST_INTENT + " or answer to his " + MOVIE_INFORMATION_REQUEST_INTENT + ". " + actions_performed
    for intention in dialogueST.get_intentions_json():
        if CREATE_NEW_LIST_INTENT in intention.keys():
            if None in intention.values():
                # ask for the name of the new list
                instruction = instruction + "The user wants to create a new movie list but hasn't specified the name of the list. Please ask the user for the name of the new list or suggest a name for the list based on the previous conversation if possible."
        elif MODIFY_EXISTING_LIST_INTENT in intention.values():
            if None in intention.values():
                # ask for the name of the list to modify, the action and the object title
                instruction= instruction + f"The user wants to modify an existing movie list but hasn't specified the name of the list, the action to perform (only actions possible: {', '.join(MODIFY_LIST_ACTIONS)}) and/or the title of the object (a movie or a series or the new name of a list). Please ask the user for these details or suggest them based on the previous conversation if possible."
        elif MOVIE_INFORMATION_REQUEST_INTENT in intention.values():
            if None in intention.values():
                # ask for the object of the information and the text of the request
                instruction = instruction + f"The user has requested movie or series information but hasn't specified the object of the information (a movie or a series) and/or the specific information requested (possible options: {', '.join(MOVIE_INFO_ACTIONS)}). Please ask the user for these details or suggest them based on the previous conversation if possible."
        elif SHOW_EXISTING_LIST_INTENT in intention.values():
            if None in intention.values():
                # ask for the name of the list to show
                instruction = instruction + "The user wants to see an existing movie list but hasn't specified the name of the list. Please ask the user for the name of the list or suggest a name for the list based on the previous conversation if possible."
        elif CANCEL_REQUEST_INTENT in intention.values():
            if None in intention.values():
                # ask for the the request to cancel
                instruction = instruction + "The user wants to cancel a previous request but you could not understand which one. Please ask the user for the request he wants to cancel."
        elif OTHER_INTENT in intention.values(): 
            # we can't manage this intent
            if not (None in intention.values()):
                request: str = intention.get("request")
                other.append(request)
            else:
                print("The other intent text of the request is empty.")
    # TODO: guardare nei json gli other intent perchè forse sono doppi, potrei averli sia in unsuccess che nelle intentions
    fallback_policy: str = ""
    if len(other) > 0:
        fallback_policy = FALLBACK_POLICY + "This are the request(s): " + "; ".join(other)
    if len(unsuccess.get_no_movie) > 0:
        movie_list_str: str = "; ".join(unsuccess.get_no_movie)
        fallback_policy = fallback_policy + unsuccess.get_other_request + " Tell the user that you were not able to find any movie or series with the given title(s): " + movie_list_str + ". Ask him if those are the correct titles."
    # other request is "" or something if needed so no problem in adding it
    instruction = instruction + fallback_policy + "This is the content of your previous conversation with the user: \"" + last_N_turns + "\".  This is the json file you are trying to fill: " + json_to_fill + " . Print only what you want to say to the user, like you are talking to him directly, and NOTHING else."
    return instruction

# Communicate to the user that all his requests have been satisfied
def completion(dialogueST: DialogueStateTracker, unsuccess: Unsuccess) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in communicateCompletion")
    fallback_policy: str = ""
    last_N_turns: str = " ".join(dialogueST.get_last_N_turns())
    if unsuccess.get_other_request != "":
        fallback_policy = FALLBACK_POLICY + "This is the text of the request(s): " + unsuccess.get_other_request
    if dialogueST.get_actions_performed() != "":
        instruction: str = "You are a movie list assistant, you helped the user with all his requests. These are the actions you have completed: " + dialogueST.get_actions_performed() + ". This is your previous conversation with the user: \"" + last_N_turns + "\". Please, inform the user that all his requests have been satisfied and if he needs further assistance." + fallback_policy + " Print ONLY what you want to say to the user, like you are talking to him directly, and NOTHING else."
    else:
        return "You are a movie list assistant, it seems that there are no actions performed to inform the user about. This is your previous conversation with the user: \"" + last_N_turns + "\"." + fallback_policy + " Please answer the user accordingly and ask if he needs further assistance. Print ONLY what you want to say to the user, like you are talking to him directly, and NOTHING else. "
    return instruction