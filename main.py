import first_interaction
import dialogue_manager
from dialogue_state_tracker import DialogueStateTracker

dialogueST: DialogueStateTracker = DialogueStateTracker()
first_interaction.runFirstInteraction(dialogueST)

while True:
    dialogue_manager.followupInteraction(dialogueST)