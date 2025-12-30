#This is the dialogue state tracker object, takes care also of the MEMORY (last N turns)

N: int = 12 # number of turns to keep in memory

class DialogueStateTracker:
    def __init__(self):
        self.intentions_json: list[str] = None # here we store the json file with the intentions of the user. They can be uncomplete (null slots) 
        self.last_N_turns: list[str] = [] # here we store the last twelve turns of the dialogue for context memory
    
    def update_intentions_json(self, json: list[str]):
        self.intentions_json = json
    
    def add_turn(self, turn: str):
        self.last_N_turns.append(turn)
        if len(self.last_N_turns) >= N: # keep only the last twelve turns removing the oldest one
            self.last_N_turns.pop(0)
    
    def get_intentions_json(self):
        return self.intentions_json
    
    def get_last_N_turns(self):
        return self.last_N_turns

