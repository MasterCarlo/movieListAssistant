# The dialogue manager chooses the next best action 

import subprocess
import time
import os
import json
import utils
from dialogue_state_tracker import DialogueStateTracker

# 
def followupInteraction(dialogueST: DialogueStateTracker, user_input: str):
    # we have to answer the user. First we must understand what is null in the json intentions. 
    # Then we must understand if we can fill the nulls with the current information or if we need more 
    # information (that we will ask to the the user)

    try:
        print("JSON intentions:", dialogueST.get_intentions_json())
        json_string: str = json.dumps(dialogueST.get_intentions_json()[0], indent=4)
    except FileNotFoundError:
        print(f"Error: {dialogueST.get_intentions_json()} not found.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file {dialogueST.get_intentions_json()}. Details: {e}")
        exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        exit(1)
    
    
    fallback = fallbackPolicy(dialogueST)
    
    # Load the last N turns of the conversation from the dialogue state tracker
    last_N_turns: list[str] = dialogueST.get_last_N_turns()
    last_N_turns_string: str = "  ".join(last_N_turns)
    system_prompt: str = ""
    # If there are null slots in the json, we need to fill them
    if "null" in json_string:
        system_prompt = f"""You are a movie list assistant and movie expert, you can help the user modifying an existing list, creating a new list or answering to his movie information requests. This is the content of your previous conversation with the user: {last_N_turns_string}. Use the content of that conversation to fill the null slots inside this json: {json_string}. If you don't find the information to fill a slot, leave it as null. Then print ONLY the filled JSON string in a JSON format and NOTHING ELSE after."""
    

    try:
        # in result we have the output of the sbatch command, so the first part of the file
        result = utils.executeSbatchCommand(sbatch_command)
        
        # now we are in marzola queue
        output_filename = utils.marzolaWaiting(result)
        
        # The file it's been created but it's not been written completely
        parsed_json = utils.marzolaJsonExtraction(output_filename)

        dialogueST.update_json_queue(parsed_json)
    
    except subprocess.CalledProcessError as e:
        print("Error occurred while executing the command:")
        print(e.stderr)
    except TimeoutError as e:
        print(f"Timeout error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def fallbackPolicy(dialogueST):
    
    try:
        intention_json: str = json.dumps(dialogueST.get_intentions_json(), indent=4)
    except FileNotFoundError:
        print(f"Error: {dialogueST.get_intentions_json()} not found.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file {dialogueST.get_intentions_json()}. Details: {e}")
        exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        exit(1)
    if "other" in intention_json:
        return "Tell the user that unfortunately we can't help him with the request that exceed from your expertise, specifying the unmanageable request that you can infer from the previous conversation. In the end, repeat him that you can help him with modifying an existing list, creating a new list or answering to his information requests."
    else:
        return " "


def answerUser(user_input: str):
    pass

if False:
    if "null" in json_string:
        system_prompt = f"""You are a movie list assistant and movie expert, you can help the user modifying an existing list, creating a new list or answering to his information requests. This is the content of your conversation with the user: {last_N_turns_string}. Use the content of that conversation and ask coherent questions to the user in order to fill the null slots inside {json_string}. If you can't fill a slot, leave it as null. {fallback}. Then print the filled JSON string in a JSON format and NOTHING ELSE after."""
    else:
        system_prompt = f"""You are a movie list assistant and movie expert, you can help the user modifying an existing list, creating a new list or answering to his information requests. This is the content of your conversation with the user: {last_N_turns_string}. Use the content of that conversation to ask coherent questions to the user, like if he needs any other help or if he is satisfied. {fallback}"""