import json
import os
import subprocess

from global_variables import *


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
        # Start the process
        process: subprocess.Popen = subprocess.Popen(command, cwd=project_root, stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                                                            stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
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