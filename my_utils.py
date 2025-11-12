import json
import os
import re
import subprocess
import time


def executeSbatchCommand(sbatch_command):
    # Execute the sbatch command
    result: str = subprocess.run(
        sbatch_command,
        universal_newlines=True,
        stdout=subprocess.PIPE,  # Capture stdout
        stderr=subprocess.PIPE,  # Capture stderr
        check=True
    )
    print("Command executed successfully!")
    print("Output:")
    print(result.stdout)
    return result


def marzolaWaiting(result: str): # non sono sicuro del tipo di result
    # Update the turns of dialogue state tracker with the user input

    # Step 2: Extract the job ID, now we are in marzola queue
    output_line: list[str] = result.stdout.strip()
    if "Submitted batch job" in output_line:
        job_id: str = output_line.split()[-1]  # Extract the job ID (last word)
        output_filename: str = f"hmd_example-{job_id}.out"
        print(f"Expected output file: {output_filename}")
    else:    
        raise ValueError("Unexpected output format from sbatch command.")

    # Step 3: Wait for the output file to be fully generated
    timeout: int = 350  # Maximum wait time in seconds
    wait_interval: int = 7  # Check every 7 seconds
    elapsed_time: int = 0
    previous_size: int = -1

    # Wait for the output file to be stable in size
    while elapsed_time < timeout:
        if os.path.exists(output_filename):
            current_size = os.path.getsize(output_filename)
            if current_size == previous_size:  # File size hasn't changed
                print(f"{output_filename} is now stable.")
                break
            previous_size = current_size
        else:
            print(f"Waiting for {output_filename} to be created...")
        time.sleep(wait_interval)
        elapsed_time += wait_interval

    if elapsed_time >= timeout:
        raise TimeoutError(f"Output file {output_filename} not stable within {timeout} seconds.")
    return output_filename


def marzolaJsonExtraction(output_filename):
    # The file it's been created but it's not been written completely.
    # We are waiting for the json part to be written by llama2
    content = ""
    json_match = re.search(r'(?s)(\{.*\})', content)
    timeout = 350  
    wait_interval = 7  # Check every 7 seconds
    elapsed_time = 0
    while elapsed_time < timeout:
        if json_match:
            break
        
        with open(output_filename, "r") as output_file:
            content = output_file.read()
            print(f"Content of {output_filename}:\n{content}")
        print(f"Waiting for json to be written: we are in queue...")
        json_match = re.search(r'(?s)(\{.*\})', content)
        time.sleep(wait_interval)
        elapsed_time += wait_interval
    
    if elapsed_time >= timeout:
        raise TimeoutError(f"Output file {output_filename} not stable within {timeout} seconds.")
        
    print(f"JSON content found: {json_match.group(1)}")
        
    # Step 4: check
    if content is None or content.strip() == "":
        raise ValueError("The output file is empty or could not be read.")   
    
    # Step 5: Use regex to extract the JSON portion of the output
    if json_match:
        json_content = json_match.group(1)  # Extract the matched JSON string
        print(f"Extracted JSON content: {json_content}")

        # Validate and save the extracted JSON
        try:
            parsed_json = json.loads(json_content)  # Ensure valid JSON
        except json.JSONDecodeError as e:
            raise ValueError(f"Extracted content is not valid JSON: {e}")
    else:
        raise ValueError("No JSON content found in the output file.")
    
    return parsed_json