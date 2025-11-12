# it chooses the next best action 

import subprocess
import time
import os
import json
import my_utils
from dialogue_state_tracker import DialogueStateTracker

# 
def followupInteraction(dialogueST: DialogueStateTracker):

    # Load the current JSON file (the first in the vector) to fill from the dialogue state tracker and convert it to a pretty-printed string for input
    try:
        json_string = json.dumps(dialogueST.get_json_queue()[0], indent=4)
    except FileNotFoundError:
        print(f"Error: {dialogueST.get_json_queue()} not found.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file {dialogueST.get_json_queue()}. Details: {e}")
        exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        exit(1)
    
    # Define the fallback policy
    fallback = fallbackPolicy(dialogueST)
    
    # Load the last six turns of the conversation from the dialogue state tracker
    last_six_turns = dialogueST.get_last_six_turns()
    last_six_turns_string = "  ".join(last_six_turns)
    system_prompt = ""
    if "null" in json_string:
        system_prompt = f"""You are a movie list assistant and movie expert, you can help the user modifying an existing list, creating a new list or answering to his information requests. This is the content of your conversation with the user: {last_six_turns_string}. Use the content of that conversation to fill the null slots inside {json_string}. If you can't fill a slot, leave it as null. Then print ONLY the filled JSON string in a JSON format and NOTHING ELSE after."""
    
    sbatch_command = [
        "sbatch",
        "--account=hmd-2024",
        "example.sbatch",
        "--system-prompt",
        system_prompt,
        "llama2",
        "User: ",
        "--max_seq_length",
        "2000"
    ]

    try:
        # in result we have the output of the sbatch command, so the first part of the file
        result = my_utils.executeSbatchCommand(sbatch_command)
        
        # now we are in marzola queue
        output_filename = my_utils.marzolaWaiting(result)
        
        # The file it's been created but it's not been written completely
        parsed_json = my_utils.marzolaJsonExtraction(output_filename)

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
        intention_json = json.dumps(dialogueST.get_intentions_json, indent=4)
    except FileNotFoundError:
        print(f"Error: {dialogueST.get_intentions_json()} not found.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file {dialogueST.get_intentions_json()}. Details: {e}")
        exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        exit(1)
    if "_other_" in intention_json:
        return "Then tell the user that unfortunately we can't help him with the request that exceed from your expertise, specifying the unmanageable request that you can infer from the previous conversation. In the end, repeat him that you can help him with modifying an existing list, creating a new list or answering to his information requests."
    else:
        return " "


if False:
    if "null" in json_string:
        system_prompt = f"""You are a movie list assistant and movie expert, you can help the user modifying an existing list, creating a new list or answering to his information requests. This is the content of your conversation with the user: {last_six_turns_string}. Use the content of that conversation and ask coherent questions to the user in order to fill the null slots inside {json_string}. If you can't fill a slot, leave it as null. {fallback}. Then print the filled JSON string in a JSON format and NOTHING ELSE after."""
    else:
        system_prompt = f"""You are a movie list assistant and movie expert, you can help the user modifying an existing list, creating a new list or answering to his information requests. This is the content of your conversation with the user: {last_six_turns_string}. Use the content of that conversation to ask coherent questions to the user, like if he needs any other help or if he is satisfied. {fallback}"""