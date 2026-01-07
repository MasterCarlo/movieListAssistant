import json
import os
import re
import subprocess
import time

from dialogue_state_tracker import DialogueStateTracker

# def marzolaJsonExtraction():
#     # We are waiting for the json part to be written by llama2
#     content = ""
#     json_match = re.search(r'(?s)(\{.*\})', content)
#     timeout = 350  
#     wait_interval = 7  # Check every 7 seconds
#     elapsed_time = 0
#     while elapsed_time < timeout:
#         if json_match:
#             break
        
#         with open(output_filename, "r") as output_file:
#             content = output_file.read()
#             print(f"Content of {output_filename}:\n{content}")
#         print(f"Waiting for json to be written: we are in queue...")
#         json_match = re.search(r'(?s)(\{.*\})', content)
#         time.sleep(wait_interval)
#         elapsed_time += wait_interval
    
#     if elapsed_time >= timeout:
#         raise TimeoutError(f"Output file {output_filename} not stable within {timeout} seconds.")
        
#     print(f"JSON content found: {json_match.group(1)}")
        
#     # Step 4: check
#     if content is None or content.strip() == "":
#         raise ValueError("The output file is empty or could not be read.")   
    
#     # Step 5: Use regex to extract the JSON portion of the output
#     if json_match:
#         json_content = json_match.group(1)  # Extract the matched JSON string
#         print(f"Extracted JSON content: {json_content}")

#         # Validate and save the extracted JSON
#         try:
#             parsed_json = json.loads(json_content)  # Ensure valid JSON
#         except json.JSONDecodeError as e:
#             raise ValueError(f"Extracted content is not valid JSON: {e}")
#     else:
#         raise ValueError("No JSON content found in the output file.")
    
#     return parsed_json

def startLLM() -> subprocess.Popen:
    try: 
        command: list[str] = ["python", "-m", "main"]
        project_root: str = os.path.abspath("../HMD-Lab")
        env: dict[str, str] = os.environ.copy()
        env["PYTHONPATH"] = project_root
        # Start the process
        process: subprocess.Popen = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                                                            stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
        time.sleep(30)  # Give some time for the process to start, it's ver slow
        print("process is:", process)
        return process
    except Exception as e:
        print(f"An error occurred while starting the LLM: {e}")
        raise


def askAndReadAnswer(process: subprocess.Popen, instruction: str) -> str:

    print("Asking LLM...")
    # We instruct the LLM with the instruction + user input
    process.stdin.write(instruction + "\n")
    process.stdin.flush()
    time.sleep(4)  # Give some time for the LLM to answer
    
    answer: list[str] = []
    while True:
        line: str = process.stdout.readline()
        if not line:
            break
        if line.strip().endswith("User:"):
            break
        answer.append(line)
    answer = "".join(answer)
    
    return answer

# we transform the dictionary json into a string with null instead of None
def jsonToString(json_list: list[dict]) -> str:
    json_str: list[str] = []
    for json_file in json_list: 
        value: str = json.dumps(json_file)
        json_str.append(value)
    json_str: str = " ".join(json_str) # we create a unique json string
    return json_str