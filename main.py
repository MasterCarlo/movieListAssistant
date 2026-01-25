import first_interaction
import dialogue_manager
import subprocess

from dialogue_state_tracker import DialogueStateTracker
from list_database import ListDatabase
from global_variables import *


# TODO: scrivere nei prompt che il sistema deve essere educato e gentile con l'utente e adattarsi a lui
dialogueST: DialogueStateTracker = DialogueStateTracker()
list_db: ListDatabase = ListDatabase()
process: subprocess.Popen = first_interaction.runFirstInteraction(dialogueST)

while True:
    if DEBUG or DEBUG_LLM:
        print("----- New follow-up interaction -----")
    dialogue_manager.followupInteraction(dialogueST, list_db, process)