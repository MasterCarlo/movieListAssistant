import subprocess
import utils
import json
import natural_language_understander as nlu

from dialogue_state_tracker import DialogueStateTracker
from global_variables import *

# run the first turn of the dialogue that is different from the others (it needs to connect to the LLM and get the first json)
def runFirstInteraction(dialogueST: DialogueStateTracker) -> subprocess.Popen:
    
    print("Wait a moment, the Movie Assistant is loading...")
        
    try:
        process: subprocess.Popen = utils.startLLM() # start "main" inside HMD-Lab folder with python -u main.py on azure 
        
        if DEBUG:
            # I behave as the LLM
            print("Debug mode: greetings")
            llmGreetings: str = input("LLM: ")
            dialogueST.add_turn("LLM: " + llmGreetings)
        else:
            if DEBUG_LLM:
                print("Reading greetings wait a moment...")
            # first we read the LLM greetings, just for debug purpose to see if it's working
            buffer: str = ""
            while True:
                ch: str = process.stdout.read(1)
                if not ch:
                    if DEBUG_LLM:
                        print("No line read, breaking")
                    break
                buffer = buffer + ch
                if buffer.endswith("User: "):
                    break
            if DEBUG_LLM:
                print("LLM greetings read:", buffer.strip("User: "))
        
        systemGreeting: str = "Movie Assistant: Hi! I am an AI agent. I am here to help you with your movie lists. If you give me a movie title, I can give you some information about it. I can add or remove movies to or from your lists, create new lists or show you the existing ones. What would you like to do today?"
        print(systemGreeting)
        dialogueST.add_turn(systemGreeting)
        user_input: str = input("User: ")
        instruction: str = "You are a movie list assistant. From the user input, I want you to extract the intentions of the user, they can be: [" + CREATE_NEW_LIST_INTENT + "], [" + MODIFY_EXISTING_LIST_INTENT + "], [" + SHOW_EXISTING_LIST_INTENT +"], ["+ MOVIE_INFORMATION_REQUEST_INTENT + "], ["+ OTHER_INTENT +"] for everything that isn't strictly one of the previously listed intents. For the " + MODIFY_EXISTING_LIST_INTENT + ", these are the ONLY action possible: [" + ", ".join(MODIFY_LIST_ACTIONS) + "]; if the action is even slightly different from these ones, the intent has to be considered [" + OTHER_INTENT + "]. For the " + MOVIE_INFORMATION_REQUEST_INTENT + ", these are the ONLY info requests possible: [" + ", ".join(MOVIE_INFO_ACTIONS) + "]; if the info request is even slightly different from these ones, the intent has to be considered [" + OTHER_INTENT + "]. Your answer must be ONLY a json format with ONLY the intentions. There can be one intention or more per user input, and the intentions can be different or the same with different data, if so, print multiple json objects inside a list, always in JSON format. For example: [{\"intention\": \"" + MOVIE_INFORMATION_REQUEST_INTENT + "\"}, {\"intention\": \"" + MODIFY_EXISTING_LIST_INTENT + "\"}, {\"intention\": \"" + MODIFY_EXISTING_LIST_INTENT + "\"}]. Here is the user input:" + user_input
        dialogueST.update_last_user_input(user_input)
        dialogueST.add_turn("User: " + user_input) # Update the turns of dialogue state tracker with the user input
        json_intentions: str = utils.askAndReadAnswer(process, instruction) # we instruct the LLM, with the user input, on how to behave. He should give us the json file with the intentions
        if DEBUG or DEBUG_LLM:
            print("JSON Answer received in first interaction: ", json_intentions)
    
    except subprocess.CalledProcessError as e:
        print("Error occurred while executing the command:")
        print(e.stderr)
        raise e
    except TimeoutError as e:
        print(f"Timeout error: {e}")
        raise e
    except Exception as e:
        print(f"Another error occurred: {e}")
        raise e
    
    intentions_list_json: list[dict] = nlu.extractIntentions(json_intentions) # from a unique string (jsonIntentions) we create a list of json strings, one for each intention, with extra information (look at intent_json_examples.json)
    dialogueST.update_intentions(intentions_list_json)
    if DEBUG or DEBUG_LLM:
        print(f"JSON content saved to dialogue state tracker in first interaction: {json.dumps(dialogueST.get_intentions_json(), indent=2)}")
    return process