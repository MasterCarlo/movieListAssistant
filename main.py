import first_interaction
import dialogue_manager
import subprocess
from dialogue_state_tracker import DialogueStateTracker

dialogueST: DialogueStateTracker = DialogueStateTracker()
user_input: str = "" 
process: subprocess.Popen = None
process = first_interaction.runFirstInteraction(dialogueST)

while True:
    dialogue_manager.followupInteraction(dialogueST, process)