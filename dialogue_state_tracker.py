#This is the dialogue state tracker object, takes care also of the MEMORY (last N turns)

N: int = 6 # number of turns to keep in memory

class DialogueStateTracker:
    def __init__(self):
        self.last_user_input: str = "" # here we store the last user input
        self.intentions_json: list[dict] = [] # here we store the json file with the intentions of the user. They can be uncomplete (null slots) 
        self.last_N_turns: list[str] = [] # here we store the last N turns of the dialogue for context memory
        self.actions_performed: str = "" # here we store the actions performed so far in the dialogue
    
    def update_last_user_input(self, user_input: str):
        self.last_user_input = user_input
    
    def update_intentions(self, json: list[dict]):
        self.intentions_json = json
    
    def update_actions(self, actions: str):
        self.actions_performed = actions
    
    def add_turn(self, turn: str):
        self.last_N_turns.append(turn)
        if len(self.last_N_turns) >= N: # keep only the last N turns removing the oldest one
            self.last_N_turns.pop(0)
    
    def clear_actions(self):
        self.actions_performed = ""
    
    def get_last_user_input(self) -> str:
        return self.last_user_input
    
    def get_intentions_json(self) -> list[dict]:
        return self.intentions_json
    
    def get_last_N_turns(self) -> list[str]:
        return self.last_N_turns
    
    def get_actions_performed(self) -> str:
        return self.actions_performed