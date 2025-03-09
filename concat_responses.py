import json

files = [
    "responses/anxiety1.json",
    "responses/anxiety2.json",
    "responses/anxiety3.json",
    "responses/anxiety4.json",

    "responses/depression1.json",
    "responses/depression2.json",
    "responses/depression3.json",
    "responses/depression4.json",

    "responses/great1.json",
    "responses/great2.json",
    "responses/great3.json",
    "responses/great4.json",
    "responses/great5.json",
    "responses/great6.json"
]

result = []

for file in files:
    with open(file) as f:
        data = json.load(f)
    result += data

with open("responses.json", 'w') as f:
    json.dump(result, f)