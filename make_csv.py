# python3 make_csv.py responses.json >responses.tsv
import json
import sys

with open(sys.argv[1]) as f:
    data = json.load(f)

print("user_id\tquestion\tresponse\tsequence_label\n")

for i, message in enumerate(data):
    message_responses = message['responses'].replace("\n\n", "\n")
    questions = list(map(lambda x: x[3:], message['question'].split('\n')[2:]))
    responses = list(map(lambda x: x[3:].strip(), message_responses.split('\n')))
    for j in range(len(questions)):
        question = questions[j]
        response = responses[j]
        print("{}\t{}\t{}\t{}".format(i+1, question, response, message['type']))