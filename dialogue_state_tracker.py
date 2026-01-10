#This is the dialogue state tracker object, takes care also of the MEMORY (last N turns)

N: int = 12 # number of turns to keep in memory

class DialogueStateTracker:
    def __init__(self):
        self.last_user_input: str = "" # here we store the last user input
        self.intentions_json: list[dict] = [] # here we store the json file with the intentions of the user. They can be uncomplete (null slots) 
        self.last_N_turns: list[str] = [] # here we store the last N turns of the dialogue for context memory
        self.action_performed: str = "" # here we store the actions performed so far in the dialogue
    
    def update_last_user_input(self, user_input: str):
        self.last_user_input = user_input
    
    def update_intentions_json(self, json: list[dict]):
        self.intentions_json = json
    
    def update_action_performed(self, action: str):
        self.action_performed = action
    
    def add_turn(self, turn: str):
        self.last_N_turns.append(turn)
        if len(self.last_N_turns) >= N: # keep only the last N turns removing the oldest one
            self.last_N_turns.pop(0)
    
    def clear_action_performed(self):
        self.action_performed = ""
    
    def get_last_user_input(self) -> str:
        return self.last_user_input
    
    def get_intentions_json(self) -> list[dict]:
        return self.intentions_json
    
    def get_last_N_turns(self) -> list[str]:
        return self.last_N_turns
    
    def get_action_performed(self) -> str:
        return self.action_performed

