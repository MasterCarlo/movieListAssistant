import json
import tmdb_api

from global_variables import *
from natural_language_generator import Unsuccess

#Open the file and read the JSON content
try:
    with open("intent_json_examples.json", "r") as file:
        data = json.load(file)
except FileNotFoundError:
    print("Error: intent_json_examples.json not found.")
    exit(1)
except json.JSONDecodeError:
    print("Error: Invalid JSON format.")
    exit(1)

# Print the data to check the contents

def json_to_single_line_string(data):
    """
    Convert a loaded JSON object into a one-line printable JSON string.
    """
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)

# print("these are the data\n" + json.dumps(data, indent=2))
# string = json_to_single_line_string(data)
# print("this is the string\n" + string)
# if string.startswith('[' or '{') and string.endswith(']' or '}'):
#     print("The provided string is a valid JSON array.")

# json_list: list[dict] = []
# json_string = json.dumps(data)
# if json_string.startswith('[') and json_string.endswith(']'):
#     try:
#         json_list = json.loads(json_string)
#     except json.JSONDecodeError as e:
#         print(f"Error decoding JSON string: {e}")
# else:
#     print("The provided string is not a valid JSON array.")

# print("this is the json_list\n" + json.dumps(json_list, indent=2))  


# Check for None (null) values in the dictionary

# for intention in data:
#     if None in intention.values():
#         print("There are null slots in the intent JSON examples.")
# if any(value is None for item in data for value in item.values()):
#     print("There are null slots in the intent JSON examples.")
# else:
#     print("All slots are filled in the intent JSON examples.")

# ================================================================================================

# intent: dict = json.loads("""{"intent": "show existing list", "list_name": null, "fulfilled": false}""")
# intent2: dict = json.loads("""{"intent":""" + """\"""" + SHOW_EXISTING_LIST_INTENT + """\", "list_name": null, "fulfilled": false}""")
# print("Intent 1:", intent)
# print("Intent 2:", intent2)

# ================================================================================================

# string: str =     """{
#         "intent": "other",
#         "text_of_the_request": "Find me movies with time travel themes."
#     }"""
# if not "null" in string:
#     data: dict = json.loads(string)
#     request: str = data["text_of_the_request"]
#     print(request)
# else:
#     print("There are null slots in the intent JSON examples.")
# print("Ciao! Come ti chiami?")
# nome = input()
# print("il tuo nome è:", nome)

# ================================================================================================

# string: str = f"""[{{"intention": "{MOVIE_INFORMATION_REQUEST_INTENT}"}}]"""
# print(string)

# ================================================================================================

# API_KEY = "037ff6ba26f3d5215cef3868aa3c8f73"
# db = tmdb_api.MovieDatabase(API_KEY)
# movies = db.search_titles("Breaking Bad", num_results=5)
# for movie in movies:
#     # print(type(movie))
#     media_type = movie.get("type")  # Default to "movie" if not specified
#     print(media_type)

# ================================================================================================

# dictionary = {
#     "Inception": {"year": 2010, "rate": 8.8},
#     "Interstellar": {"year": 2014, "rate": 8.6},
#     "things_I_like": ["movies", "music", "programming"],
#     "list": "TUTTO MAIUSCOLO"
# }

# dictionary["Inception"]["director"] = "Christopher Nolan"

# # print(dictionary.get("things_I_like"))
# # print(dictionary.get("not_existing_key", "Default Value"))
# print(dictionary.get("list"))
# print(dictionary.get("list")[0])
# print(type(dictionary.get("list")))
# print(dictionary.get("list").lower())


# ================================================================================================

# string: str = "User: "
# if string.strip().endswith("User:"):
#     print(string)
# else:
#     print("No match")

# ================================================================================================

#MCRSFT ZUR UN: disi
# p: #Occhialini1

# ================================================================================================

# unsuccess: Unsuccess = Unsuccess()
# string: str = "roba varia"
# unsuccess.add_no_movie("Inception")
# unsuccess.add_other_request("Find me movies with time travel themes.")
# if isinstance(unsuccess, Unsuccess):
#     print("unsuccess is Unsuccess")
# else:
#     print("unsuccess is NOT Unsuccess")
# if isinstance(string, str):
#     print("string is str")
# else:
#     print("string is NOT str")
# if isinstance(string, Unsuccess):
#     print("string is Unsuccess")
# else:
#     print("string is NOT Unsuccess")