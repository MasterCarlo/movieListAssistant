class ListDatabase:
    def __init__(self):
        self.lists: dict[str, dict] = {}

    def get_list(self, list_name: str):
        return self.lists.get(list_name, None)
    def get_all_lists(self) -> dict[str, dict]:
        return self.lists
