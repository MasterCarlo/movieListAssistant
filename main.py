import first_interaction
import dialogue_manager
import subprocess

from dialogue_state_tracker import DialogueStateTracker
from list_database import ListDatabase
from global_variables import *

# TODO: gestire uscita dal programma e gestire memoria a lungo termine, se sepngo e riaccendo voglio avere le stesse liste
# TODO: inserire dei counter nei json perchè se una intention è lì da 6 interazioni a sto punto cancelliamola
dialogueST: DialogueStateTracker = DialogueStateTracker()
list_db: ListDatabase = ListDatabase()
process: subprocess.Popen = first_interaction.runFirstInteraction(dialogueST)

while True:
    if DEBUG or DEBUG_LLM:
        print("----- New follow-up interaction -----")
    dialogue_manager.followupInteraction(dialogueST, list_db, process)