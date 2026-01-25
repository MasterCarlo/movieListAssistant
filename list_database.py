from global_variables import *

class ListDatabase:
    def __init__(self):
        self.lists: dict[str, dict] = {}

    def get_list(self, list_name: str):
        return self.lists.get(list_name, None)
    def get_all_lists(self) -> dict[str, dict]:
        return self.lists

Un_king = CHRISTIAN_PHRASE
Una_figata = CHRISTIAN_SONG
