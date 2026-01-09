import first_interaction
import dialogue_manager
import subprocess

from dialogue_state_tracker import DialogueStateTracker
from list_database import ListDatabase


dialogueST: DialogueStateTracker = DialogueStateTracker()
list_db: ListDatabase = ListDatabase()
process: subprocess.Popen = first_interaction.runFirstInteraction(dialogueST)

while True:
    dialogue_manager.followupInteraction(dialogueST, list_db,process)