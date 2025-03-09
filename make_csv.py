# python3 make_csv.py responses.json >responses.tsv
import json
import sys

file = sys.argv[1] if len(sys.argv) > 1 else "responses.json"
with open(file) as f:
    data = json.load(f)

with open("responses.tsv", 'w') as out:
    print("user_id\tquestion\tresponse\tsequence_label\n", file=out)

    for i, message in enumerate(data):
        message_responses = message['responses'].replace("\n\n", "\n")
        questions = list(map(lambda x: x[3:], message['question'].split('\n')[2:]))
        responses = list(map(lambda x: x[3:].strip(), message_responses.split('\n')))
        for j in range(len(questions)):
            question = questions[j]
            response = responses[j]
            print("{}\t{}\t{}\t{}".format(i+1, question, response, message['type']), file=out)

    out.flush()