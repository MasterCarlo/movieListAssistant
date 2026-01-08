import json

# #Open the file and read the JSON content
# try:
#     with open("intent_json_examples.json", "r") as file:
#         data = json.load(file)
# except FileNotFoundError:
#     print("Error: intent_json_examples.json not found.")
#     exit(1)
# except json.JSONDecodeError:
#     print("Error: Invalid JSON format.")
#     exit(1)

# # Print the data to check the contents
# print("these are the data\n" + json.dumps(data, indent=2))

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

# string: str = """[]"""
# print(len(string))

onelist = [1,2,3,4]
anotherlist = [5,6,7]
# onelist.extend(anotherlist)
anotherlist.extend(onelist)
print(anotherlist)

