import json
import os
import subprocess

from global_variables import *
from dialogue_state_tracker import DialogueStateTracker
from natural_language_generator import Unsuccess

def startLLM() -> subprocess.Popen:
    
    if DEBUG:
        print("DEBUG mode is ON: LLM process will not be started.")
        return None 
    if DEBUG_LLM:
        print("DEBUG_LLM mode is ON: starting LLM process...")
    try: 
        command: list[str] = ["python", "-u","main.py"]
        this_dir: str = os.path.dirname(os.path.abspath(__file__))
        project_root: str = os.path.abspath(os.path.join(this_dir, "..", "HMD-Lab"))
        env: dict[str, str] = os.environ.copy()
        env["PYTHONPATH"] = project_root
        # Start the process with separate stderr to capture errors
        process: subprocess.Popen = subprocess.Popen(command, cwd=project_root, stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                                                            stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
        print("Starting LLM process, please wait...")
        if DEBUG or DEBUG_LLM:
            print("process is:", process)
        return process
    except Exception as e:
        print(f"An error occurred while starting the LLM: {e}")
        raise


def askAndReadAnswer(process: subprocess.Popen, instruction: str) -> str:
    
    if DEBUG or DEBUG_LLM:
        print("DEBUG in askAndReadAnswer")
        # print("Instruction sent to LLM:", instruction)
    if DEBUG:
        answer: str = input("LLM: ")
        return answer
    # We instruct the LLM with the instruction + user input
    try:
        # Check if process is still alive
        if process.poll() is not None:
            print(f"ERROR: LLM process has terminated with exit code {process.returncode}")
            print("Process stdout before termination:")
            remaining_stdout = process.stdout.read()
            if remaining_stdout:
                print(remaining_stdout)
            print("\nProcess stderr before termination:")
            remaining_stderr = process.stderr.read()
            if remaining_stderr:
                print(remaining_stderr)
            raise RuntimeError(f"LLM process died with exit code {process.returncode}")
        
        process.stdin.write(instruction + "\n")
        process.stdin.flush()
        buffer: str = ""
        while True:
            ch = process.stdout.read(1)
            if not ch:
                if DEBUG_LLM:
                    print("No line read, breaking")
                break
            buffer = buffer + ch
            if buffer.endswith("User: "):
                break
        if DEBUG_LLM:
            print("LLM answer:", buffer.strip("User: "))
        return buffer.strip("User: ").strip("System: ").strip()


    except Exception as e:
        print(f"An error occurred while writing/reading to LLM stdin: {e}")
        raise e

# Transform the list of dictionary json into a string with null instead of None. it's a one line string
# because the shell can't manage multi line text
def jsonToString(json_list: list[dict]) -> str:

    json_str: str = json.dumps(json_list, separators=(",", ":"), ensure_ascii=False)
    return json_str

# Transform a json string into a list of dict with None instead of null
def stringToJson(json_string: str) -> list[dict]:
    json_list: list[dict] = []
    json_string = json_string.strip()
    if json_string.startswith('[' or '{') and json_string.endswith(']' or '}'):
        try:
            json_list = json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON string: {e}")
    else:
        print("The provided string is not a valid JSON array.")
    return json_list


# Qwen3 is stupid we need to check
def llmSupervision(dialogueST: DialogueStateTracker) -> Unsuccess:
    
    def modifyOrInfo(intention: dict) -> list[str] | bool:
        if MODIFY_EXISTING_LIST_INTENT in intention.values() and (intention.get("action")[0] is not None):
            return MODIFY_LIST_ACTIONS
        if MOVIE_INFORMATION_REQUEST_INTENT in intention.values() and (intention.get("information_requested")[0] is not None):
            return MOVIE_INFO_ACTIONS
        return False
    
    intentions: list[dict] = dialogueST.get_intentions_json()
    if DEBUG or DEBUG_LLM:
        print("DEBUG in llmSupervision")
        print("Filled JSON list to supervise:", json.dumps(intentions, indent=2))
    unsuccess: Unsuccess = Unsuccess()
    updated_intentions: list[dict] = []
    invalid: bool = False
    updated: bool = False
    for intent in intentions:
        if intent.get("intent") not in [CREATE_NEW_LIST_INTENT, MODIFY_EXISTING_LIST_INTENT, SHOW_EXISTING_LIST_INTENT, MOVIE_INFORMATION_REQUEST_INTENT, CANCEL_REQUEST_INTENT, OTHER_INTENT]:
            if DEBUG or DEBUG_LLM:
                print(f"LLM supervision: intent '{intent.get('intent')}' is not valid. Dropping it.")
            unsuccess.add_other_request(intent.get("intent"))
            updated = True
            continue # skip invalid intents
        intent["fulfilled"] = False # reset fulfilled to false in case of QWEN3 being stupid
        actions: list[str] = modifyOrInfo(intent)
        invalid = False
        if actions:
            query: list[str] = intent.get("action", intent.get("information_requested", [])) # return to query the action or the information_requested
            valid_actions: list[str] = actions
            filtered_query: list[str] = []
            repair: str | bool = False
            for q in query:
                if repair := repairAction(q, valid_actions): # if q is a valid action or a substring of it (meaning QWEN3 fked up but not so much, es: "director" instead if "get director")
                    filtered_query.append(repair)
                    updated = True
                else: # if q is not  avalid action at all
                    if DEBUG or DEBUG_LLM:
                        print(f"LLM supervision: action '{q}' is not valid. Deleting it.")
                    unsuccess.add_other_request(q)
                    invalid = True
                    updated = True
            if MODIFY_EXISTING_LIST_INTENT in intent.values():
                intent["action"] = filtered_query
                if (not invalid) or ((not intent.get("action") == []) and (not intent.get("action") is None)): # if after filtering it's not empty we keep it, else we drop it because it was a fully invalid request. If it was already empty (invalid == False) we keep it to ask the user later
                    updated_intentions.append(intent)
            else:
                intent["information_requested"] = filtered_query
                if (not invalid) or ((not intent.get("information_requested") == []) and (not intent.get("information_requested") is None)): # if after filtering it's not empty we keep it, else we drop it because it was a fully invalid request. If it was already empty (invalid == False) we keep it to ask the user later
                    updated_intentions.append(intent)
    if updated:
        dialogueST.update_intentions(updated_intentions)
    if DEBUG or DEBUG_LLM:
        print("Filled JSON list after LLM supervision:", json.dumps(intentions, indent=2))
    return unsuccess

# Try to find the closest action in valid_actions to query for now we do a simple substring match
def repairAction(query: str, valid_actions: list[str]) -> str | bool:
    for action in valid_actions:
        if query in action or action in query:
            return action
    return False