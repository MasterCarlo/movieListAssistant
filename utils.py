import json
import os
import subprocess

from global_variables import *
from movieListAssistant.dialogue_state_tracker import DialogueStateTracker


def startLLM() -> subprocess.Popen:
    
    if DEBUG:
        print("DEBUG mode  is ON: LLM process will not be started.")
        return None  
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
def llmSupervision(dialogueST: DialogueStateTracker) -> str:
    
    filled_json_list: list[dict] = dialogueST.get_intentions_json()
    if DEBUG or DEBUG_LLM:
        print("DEBUG in llmSupervision")
        print("Filled JSON list to supervise:", json.dumps(filled_json_list, indent=2))
    other_request: str = ""
    for intention in filled_json_list:
        if MODIFY_EXISTING_LIST_INTENT in intention.values():
            actions: list[str] = intention.get("action", [])
            valid_actions: list[str] = MODIFY_LIST_ACTIONS.replace('"', '').split(", ")

            filtered_actions: list[str] = []
            for action in actions:
                if action not in valid_actions:
                    print(f"LLM supervision: action '{action}' is not valid. Deleting it.")
                    other_request = other_request + "; " + action
                else:
                    filtered_actions.append(action)

            intention["action"] = filtered_actions

        elif MOVIE_INFORMATION_REQUEST_INTENT in intention.values():
            info_requested: list[str] = intention.get("information_requested", [])
            valid_info: list[str] = MOVIE_INFO_ACTIONS.replace('"', '').split(", ")

            filtered_info: list[str] = []
            for info in info_requested:
                if info not in valid_info:
                    print(
                        f"LLM supervision: information requested '{info}' is not valid. Deleting it."
                    )
                    other_request = other_request + "; " + info
                else:
                    filtered_info.append(info)

            intention["information_requested"] = filtered_info
    dialogueST.update_intentions(filled_json_list)
    if DEBUG or DEBUG_LLM:
        print("Filled JSON list after LLM supervision:", json.dumps(filled_json_list, indent=2))
    return other_request