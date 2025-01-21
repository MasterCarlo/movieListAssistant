import subprocess
import time
import os
import json
import re



from natural_language_understander import extractIntentionsJson

def runFirstInteraction(dialogueST):
    print("Hi! I am here to help you with your movie lists. I can give you information about movies, add or remove movies to or from your lists and create new lists. What would you like to do today?")

    # Define the user input, it should be keyboard input but now we stay like this for speed
    user_input = "User: I'd like to add Avatar to the list of watched movies. I'd also like some information about Avatar"

    # Define the sbatch command
    sbatch_command = [
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

    dialogueST.add_turn(('user', sbatch_command[6]))

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
        wait_interval = 7  # Check every 7 seconds
        elapsed_time = 0
        previous_size = -1

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
        
        # now we are in marzola queue, the file it's been created but it's not been written completely.
        # We are waiting for the json part to be written by llama2
        
        elapsed_time = 0
        content = ""
        json_match = re.search(r'(?s)(\{.*\})', content)
        timeout = 300  
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
                dialogueST.update_intentions_json(parsed_json)
                print(f"JSON content saved to dialogue state tracker: {dialogueST.get_intentions_json()}")
            except json.JSONDecodeError as e:
                raise ValueError(f"Extracted content is not valid JSON: {e}")
        else:
            raise ValueError("No JSON content found in the output file.")

    except subprocess.CalledProcessError as e:
        print("Error occurred while executing the command:")
        print(e.stderr)
    except TimeoutError as e:
        print(f"Timeout error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    intentions_json_list = extractIntentionsJson(dialogueST)
    dialogueST.update_json_queue(intentions_json_list)
