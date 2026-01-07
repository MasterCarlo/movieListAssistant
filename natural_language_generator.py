import json

from global_variables import *
from dialogue_state_tracker import DialogueStateTracker

# We generate a question to ask the user to fill the null slots in the json intentions.
# filled_json is the json with the intentions filled as much as possible with previous information, 
# but it still has null slots
def generate_question(dialogueST: DialogueStateTracker, last_N_turns: str, filled_json: str) -> str:
    
    instruction: str = "You are a movie list assistant and movie expert, you can help the user only modifying an existing list, creating a new list or answering to his movie information requests."
    for intention in dialogueST.get_intentions_json():
        if CREATE_NEW_LIST_INTENT in intention:
            if "null" in intention:
                # ask for the name of the new list
                instruction= instruction + "The user wants to create a new movie list but hasn't specified the name of the list. Please ask the user for the name of the new list or suggest a name for the list based on the previous conversation if possible."
        elif MODIFY_LIST_INTENT in intention:
            if "null" in intention:
                # ask for the name of the list to modify, the action and the object title
                instruction= instruction + "The user wants to modify an existing movie list but hasn't specified the name of the list, the action to perform (only actions possible: \"add object\", \"remove object\", \"delete list\") and/or the title of the object (a movie or a series). Please ask the user for these details or suggest them based on the previous conversation if possible."
        elif MOVIE_INFO_REQUEST_INTENT in intention:
            if "null" in intention:
                # ask for the object of the information and the text of the request
                instruction= instruction + "The user has requested movie information but hasn't specified the object of the information (a movie or a series) and/or the text of the request. Please ask the user for these details or suggest them based on the previous conversation if possible."
        elif SHOW_EXISTING_LIST_INTENT in intention:
            if "null" in intention:
                # ask for the name of the list to show
                instruction= instruction + "The user wants to see an existing movie list but hasn't specified the name of the list. Please ask the user for the name of the list or suggest a name for the list based on the previous conversation if possible."
        elif OTHER_INTENT in intention:
            # we can't manage this intent
            request: str = ""
            if not "null" in intention:
                data: dict = json.loads(intention)
                request: str = "The text of the request is " + data[OTHER_INTENT]["request"]
            else:
                print("The other intent text of the request is empty.")
            instruction = instruction + "The user has made a request that exceeds your expertise. Please politely inform the user that you are unable to assist with that particular request." + request + ". Then, remind the user that you can help him with modifying an existing list, creating a new list or answering to his movie information requests." 
    
    instruction = instruction + "This is the content of your previous conversation with the user: " + last_N_turns + "  This is the json file you are trying to fill: " + filled_json + " . Print only what you want to say to the user, like you are talking to him directly, and NOTHING else."
    return instruction