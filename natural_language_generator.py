import utils
import subprocess

from global_variables import *
from dialogue_state_tracker import DialogueStateTracker
from list_database import ListDatabase


# a class to store all the unsuccessful outcomes during the dialogue, so that we can inform the user later
class Unsuccess:
    def __init__(self):
        self.no_movie: list[str] = [] # list of movie titles not found
        self.no_list: list[str] = [] # list of list names not found
        self.other_request: list[str] = [] # text of out of bound requests (i.e. asking for movie country)
    def add_no_movie(self, title: str):
        self.no_movie.append(title)
    def add_no_list(self, list_name: str):
        self.no_list.append(list_name)
    def add_other_request(self, request: str):
        self.other_request.append(request)
    def get_no_movie(self) -> list[str]:
        return self.no_movie
    def get_no_list(self) -> list[str]:
        return self.no_list
    def get_other_request(self) -> list[str]:
        return self.other_request
    def clear(self):
        self.no_movie = []
        self.no_list = []
        self.other_request = []
    def merge(self, other: 'Unsuccess'):
        self.no_movie.extend(other.get_no_movie())
        self.no_list.extend(other.get_no_list())
        self.other_request.extend(other.get_other_request())


# We generate a question to ask the user to fill the null slots in the json intentions.
# json_to_fill is the json with the intentions filled as much as possible with previous information, 
# but it still has null slots
def generateLLMResponse(dialogueST: DialogueStateTracker, unsuccess: Unsuccess, list_db: ListDatabase) -> str:
    
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


    fallback_policy: str = ""
    if len(other) > 0:
        fallback_policy = FALLBACK_POLICY + "This are the request(s): " + "; ".join(other) + "; " + "; ".join(unsuccess.get_other_request())
    if len(unsuccess.get_no_movie()) > 0:
        no_movies: str = "; ".join(unsuccess.get_no_movie())
        fallback_policy = fallback_policy + " Tell the user that you were not able to find any movie or series with the given title(s): " + no_movies + ". Ask him if those are the correct titles."    
    if len(unsuccess.get_no_list()) > 0:
        no_lists: str = "; ".join(unsuccess.get_no_list())
        fallback_policy = fallback_policy + " Tell the user that the following list(s) do not exist: " + no_lists + ". Ask him if those are the correct list names."
    existing_lists: str = ""
    if len(list_db.get_all_lists()) > 0:
        existing_lists = ALL_LISTS + list_db.get_all_lists().keys().__str__() + "."
    instruction = instruction + existing_lists + fallback_policy + "This is the content of your previous conversation with the user: \"" + last_N_turns + "\".  This is the json file you are trying to fill: " + json_to_fill + " . Print only what you want to say to the user, like you are talking to him directly, and NOTHING else. Be kind and adapt to the user personality"
    unsuccess.clear()
    return instruction

# Communicate to the user that all his requests have been satisfied
def completion(dialogueST: DialogueStateTracker, unsuccess: Unsuccess) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in communicateCompletion")
    fallback_policy: str = ""
    last_N_turns: str = " ".join(dialogueST.get_last_N_turns())
    if len(unsuccess.get_other_request()) > 0:
        fallback_policy = FALLBACK_POLICY + "This is the text of the request(s): " + "; ".join(unsuccess.get_other_request())
    if len(unsuccess.get_no_movie()) > 0:
        no_movies: str = "; ".join(unsuccess.get_no_movie())
        fallback_policy = fallback_policy + " Tell the user that you were not able to find any movie or series with the given title(s): " + no_movies + ". Ask him if those are the correct titles."
    if len(unsuccess.get_no_list()) > 0:
        no_lists: str = "; ".join(unsuccess.get_no_list())
        fallback_policy = fallback_policy + " Tell the user that the following list(s) do not exist: " + no_lists + ". Ask him if those are the correct list names."
    if dialogueST.get_actions_performed() != "":
        instruction: str = "You are a movie list assistant, you helped the user with all his requests. These are the actions you have completed: " + dialogueST.get_actions_performed() + ". This is your previous conversation with the user: \"" + last_N_turns + "\". Please, inform the user that all his requests have been satisfied and if he needs further assistance." + fallback_policy + " Print ONLY what you want to say to the user, like you are talking to him directly, and NOTHING else."
    else:
        return "You are a movie list assistant, it seems that there are no actions performed to inform the user about. This is your previous conversation with the user: \"" + last_N_turns + "\"." + fallback_policy + " Please answer the user accordingly and ask if he needs further assistance. Print ONLY what you want to say to the user, like you are talking to him directly, and NOTHING else. "
    unsuccess.clear()
    dialogueST.clear_actions() # clear actions for the next interactions
    return instruction


def askUser(process: subprocess.Popen, dialogueST: DialogueStateTracker, unsuccess: Unsuccess, list_db: ListDatabase) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in askUser")
    instruction: str = ""
    # We generate the question for the user for more information. Inside the question there is also the 
    # communication of previously performed actions or failure to fulfill something out of boundaries
    instruction= generateLLMResponse(dialogueST, unsuccess, list_db)
    llmAnswer: str = utils.askAndReadAnswer(process, instruction) # the LLM actually asks the user something. It also communicate any action performed so far and any fallback policy (if the user requested something outside the boundaries of the system)
    print("Movie Assistant:", llmAnswer)
    # If the user had an other intent, we already answered him that we can't handle it, so we fulfilled it. 
    # We mark it as fulfilled so we don't ask again later. It's for safety, should be already fulfilled
    for intention in dialogueST.get_intentions_json():
        if intention.get("intent") == OTHER_INTENT:
            intention["fulfilled"] = True
    dialogueST.add_turn("Movie Assistant: " + llmAnswer)
    userInput: str = input("User: ")
    dialogueST.update_last_user_input(userInput)
    dialogueST.add_turn("User: " + userInput)
    return userInput