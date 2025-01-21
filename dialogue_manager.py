# it chooses the next best action 

import subprocess
import time
import os
import json

# 
def followupInteraction(dialogueST):
    
    # Load the JSON content from the dialogue state tracker and convert JSON content to a pretty-printed string for input
    try:
        json_string = json.dumps(dialogueST.get_json_queue(), indent=4)
    except FileNotFoundError:
        print(f"Error: {dialogueST.get_json()} not found.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file {dialogueST.get_json()}. Details: {e}")
        exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        exit(1)

    # Define the sbatch command
    sbatch_command = [
        "sbatch",
        "--account=hmd-2024",
        "example.sbatch",
        "--system-prompt",
        f"""You are a movie list assistant and movie expert, this is the content previuosly gained in a json format: {json_string}. Ask the user, choosing from the slots with null values, one question in order to fill one slot. This are the possible choices: [cooking style: [raw], [medium], [well done]], [sauce: [mushroom champignon sauce],[no sauce]], [salt: [low], [medium], [salty]], [meat type: [beef], [bison], [buffalo]], [count: [integer]], [size: [small], [medium], [big]]""",
        "llama2",
        "User: ",
        "--max_seq_length",
        "1500"
    ]

    try:
        # Execute the sbatch command
        result = subprocess.run(
            sbatch_command,
            universal_newlines=True,
            stdout=subprocess.PIPE,  # Capture stdout
            stderr=subprocess.PIPE,  # Capture stderr
            check=True
        )
        print("Command executed successfully!")
        print("Output:")
        print(result.stdout)

        # Step 2: Extract the job ID
        output_line = result.stdout.strip()
        if "Submitted batch job" in output_line:
            job_id = output_line.split()[-1]  # Extract the job ID (last word)
            output_filename = f"hmd_example-{job_id}.out"
            print(f"Expected output file: {output_filename}")
        else:
            raise ValueError("Unexpected output format from sbatch command.")

        # Step 3: Wait for the output file to be fully generated
        timeout = 300  # Maximum wait time in seconds
        wait_interval = 5  # Check every 5 seconds
        elapsed_time = 0
        previous_size = -1

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
        
        # now we are in marzola queue, the file it's been created but it's not been written completely.
        # We are waiting for the output to be written by llama2
        
        elapsed_time = 0
        content = ""
        timeout = 300
        specific_string = "Some parameters are on the meta device device because they were offloaded to the cpu."
        while elapsed_time < timeout:
            with open(output_filename, "r") as output_file:
                content = output_file.read()
            print(f"Content of {output_filename}:\n{content}")
            
            # we look for the question in the file, we are still in marzola queue 
            if specific_string in content:
                # Find the content after the specific string
                index = content.find(specific_string) + len(specific_string)
                following_text = content[index:].strip()
                if following_text:  # If there is text after the specific string
                    dialogueST.add_turn(following_text)
                    print(f"Output saved to dialogue state tracker: {dialogueST.get_last_six_turns()[-1]}")
                    break
                else:
                    print(f"Specific string '{specific_string}' found, but no additional text yet.")
            
            print(f"Waiting for question to be written: we are in queue...")
            time.sleep(wait_interval)
            elapsed_time += wait_interval
        
        if elapsed_time >= timeout:
            raise TimeoutError(f"Output file {output_filename} not stable within {timeout} seconds.")
        
        # Step 4: check
        if content is None or content.strip() == "":
            raise ValueError("The output file is empty or could not be read.")
        
        # Validate and save the extracted question

    except subprocess.CalledProcessError as e:
        print("Error occurred while executing the command:")
        print(e.stderr)
    except TimeoutError as e:
        print(f"Timeout error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")