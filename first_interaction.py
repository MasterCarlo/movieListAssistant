import subprocess
import utils
import json
import natural_language_understander as nlu

from dialogue_state_tracker import DialogueStateTracker
from global_variables import *

# run the first turn of the dialogue that is different from the others (it needs to connect to the LLM and get the first json)
def runFirstInteraction(dialogueST: DialogueStateTracker) -> subprocess.Popen:
    systemGreeting: str = "Hi! I am an AI agent. I am here to help you with your movie lists. I can give you information about movies, add or remove movies to or from your lists, create new lists or show you the existing ones. I can offer you suggestions to improve your movie experience. What would you like to do today?"
    print(systemGreeting)
    dialogueST.add_turn("System: " + systemGreeting)
    
    try:
        process: subprocess.Popen = utils.startLLM() # start "main" inside HMD-Lab folder with python -m main on azure 
        
        # first we read the LLM greetings, just for debug purpose to see if it's working
        greetings: list[str] = []
        while True:
            line: str = process.stdout.readline()
            if not line:
                break
            print("Line read from LLM:", line) # Debug print
            if line.strip().endswith("User:"): # If the last line is only "User:" it means the LLM has finished the greetings
                break
            greetings.append(line)
        print("LLM Greetings:", "".join(greetings))
        # Define the user input, it should be keyboard input but now we stay like this for speed
        # user_input: str = "I'd like to add Avatar to the list of watched movies. I'd also like some information about Avatar"
        user_input: str = input("User: ")
        instruction: str = "You are a movie expert. From the user input, I want you to extract the intentions of the user, they can be: [" + CREATE_NEW_LIST_INTENT + "], [" + MODIFY_EXISTING_LIST_INTENT + "], [" + SHOW_EXISTING_LIST_INTENT +"], ["+ MOVIE_INFORMATION_REQUEST_INTENT + "], ["+ OTHER_INTENT +"]. Your answer must be ONLY a json format with ONLY the intentions. There can be one intention or more per user input, and the intentions can be different or the same with different data, if so, print multiple json objects inside a list, always in JSON format. For example: [{\"intention\": \"movie information request\"}, {\"intention\": \"modify existing list\"}, {\"intention\": \"modify existing list\"}]. Here is the user input:" + user_input # + ".The json format must be like this: {\"intent\": \"create new list\", \"list_name\": null} for create new list, {\"intent\": \"modify existing list\", \"list_name\": null, \"action\": null, \"object_title\": null} for modify existing list, {\"intent\": \"show existing list\", \"list_title\": null} for show existing list, {\"intent\": \"movie information request\", \"object_of_the_information\": null, \"text_of_the_request\": null} for information request, {\"intent\": \"other\", \"text_of_the_request\": null} for other. If there are multiple intentions, print multiple json objects inside a list, always in JSON format. For example: [{\"intent\": \"create new list\", list name: null}, {\"intent\": \"information request\", \"object of the information\": null, \"text of the request\": null}]"
        dialogueST.add_last_user_input(user_input)
        dialogueST.update_turns(user_input) # Update the turns of dialogue state tracker with the user input
        json_intentions: str = utils.askAndReadAnswer(process, instruction) # we instruct the LLM, with the user input, on how to behave. He should give us the json file with the intentions
        print("JSON Answer received: ", json_intentions)

        # maybe first we have to extract the json from the llm (if he says some bullshit like "for sure, here is the json: {...}")
        # marzolajsonextraction
    
    except subprocess.CalledProcessError as e:
        print("Error occurred while executing the command:")
        print(e.stderr)
    except TimeoutError as e:
        print(f"Timeout error: {e}")
    except Exception as e:
        print(f"Another error occurred: {e}")
    
    intentions_list_json: list[dict] = nlu.extractIntentions(json_intentions) # from a unique string (jsonIntentions) we create a list of json strings, one for each intention, with extra information (look at intent_json_examples.json)
    dialogueST.update_intentions_json(intentions_list_json)
    print(f"JSON content saved to dialogue state tracker: {json.dumps(dialogueST.get_intentions_json(), indent=2)}")
    return process