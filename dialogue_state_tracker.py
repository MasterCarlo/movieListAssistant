class DialogueStateTracker:
    def __init__(self):
        self.intentions_json = None
        self.json_queue = None
        self.last_six_turns: list[str] = []
    
    def update_intentions_json(self, json):
        self.intentions_json = json
    
    def update_json_queue(self, json_list):
        for json in json_list:
            self.json_queue.append(json)
    
    def add_turn(self, turn):
        self.last_six_turns.append(turn)
        if len(self.last_six_turns) >= 6:
            self.last_six_turns.pop(0)
    
    def get_intentions_json(self):
        return self.intentions_json
    
    def get_json_queue(self):
        return self.json_queue
    
    def get_last_six_turns(self):
        return self.last_six_turns

