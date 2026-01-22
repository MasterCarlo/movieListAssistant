#DEBUG
DEBUG: bool = False
DEBUG_LLM: bool = False

# INTENTS
CREATE_NEW_LIST_INTENT: str = "create new list"
MOVIE_INFORMATION_REQUEST_INTENT: str = "movie or series information request"
MODIFY_EXISTING_LIST_INTENT: str = "modify existing list"
SHOW_EXISTING_LIST_INTENT: str = "show existing list/all lists"
CANCEL_REQUEST_INTENT: str = "cancel previous intent"
OTHER_INTENT: str = "other"

# ACTIONS
MODIFY_LIST_ACTIONS: list[str] = ["add object", "remove object", "change title", "delete list"]
MOVIE_INFO_ACTIONS: list[str] = ["get cast", "get director", "get year", "get genre", "get ratings", "get plot", "get duration"]

# FALLBACK POLICY
FALLBACK_POLICY: str = "The user has made a request that exceeds your expertise. Please politely inform the user that you are unable to assist with that particular request. Then, remind the user that you can help him with" + MODIFY_EXISTING_LIST_INTENT + ", " + CREATE_NEW_LIST_INTENT + " or answering to his " + MOVIE_INFORMATION_REQUEST_INTENT + "."