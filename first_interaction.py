import subprocess
import my_utils

from dialogue_state_tracker import DialogueStateTracker
from natural_language_understander import extractIntentionsJson

def runFirstInteraction(dialogueST: DialogueStateTracker):
    print("Hi! I am an AI agent. I am here to help you with your movie lists. I can give you information about movies, add or remove movies to or from your lists and create new lists. I can offer you suggestions to improve your movie experience. What would you like to do today?")

    # Define the user input, it should be keyboard input but now we stay like this for speed
    user_input: str = "User: I'd like to add Avatar to the list of watched movies. I'd also like some information about Avatar"

    # Define the sbatch command
    sbatch_command: list[str] = [
        "sbatch",
        "--account=hmd-2024",
        "example.sbatch",
        "--system-prompt",
        """You are a movie expert. From the user input, I want you to extract the intentions of the user, it can be: [create new list], [modify existing list], [information request], [other]. You must print ONLY a json format with the intentions. There can be more than one intention per input, if so, print them in one unique json.""",
        "llama2",
        f"User: {user_input}",
        "--max_seq_length",
        "1500"
        ]

    # Update the turns of dialogue state tracker with the user input
    dialogueST.add_turn((sbatch_command[6]))

    try:
        result: str = my_utils.executeSbatchCommand(sbatch_command)

        # now we are in marzola queue
        output_filename = my_utils.marzolaWaiting(result)
        
        # The file has been created but it's not been written completely
        parsed_json = my_utils.marzolaJsonExtraction(output_filename)
        
        dialogueST.update_intentions_json(parsed_json)
        print(f"JSON content saved to dialogue state tracker: {dialogueST.get_intentions_json()}")
    
    except subprocess.CalledProcessError as e:
        print("Error occurred while executing the command:")
        print(e.stderr)
    except TimeoutError as e:
        print(f"Timeout error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    intentions_json_list = extractIntentionsJson(dialogueST)
    dialogueST.update_json_queue(intentions_json_list)
