import json

# Open the file and read the JSON content
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
print("these are the data" + json.dumps(data, indent=2))

# Check for None (null) values in the dictionary

for intention in data:
    if None in intention.values():
        print("There are null slots in the intent JSON examples.")
# if any(value is None for item in data for value in item.values()):
#     print("There are null slots in the intent JSON examples.")
# else:
#     print("All slots are filled in the intent JSON examples.")

string: str =     """{
        "intent": "other",
        "text_of_the_request": "Find me movies with time travel themes."
    }"""
if not "null" in string:
    data: dict = json.loads(string)
    request: str = data["text_of_the_request"]
    print(request)

else:
    print("There are null slots in the intent JSON examples.")
# print("Ciao! Come ti chiami?")
# nome = input()
# print("il tuo nome è:", nome)