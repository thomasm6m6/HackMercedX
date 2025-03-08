import json
import os
import time
import random
from itertools import combinations
from openai import OpenAI

questions = [
    "How was your energy yesterday?",
    "What's on your mind lately?",
    "How have you been sleeping?",
    "Feeling overwhelmed at all?",
    "How's your focus been?",
    "Any big worries today?",
    "How's your mood been?"
]

def is_valid_schedule(schedule):
    # Check if each question appears exactly twice
    count = {q: 0 for q in questions}
    for day in schedule:
        count[day[0]] += 1
        count[day[1]] += 1

    return all(c == 2 for c in count.values())

def generate_schedules(limit):
    all_pairs = list(combinations(questions, 2))
    schedules = []

    for schedule in combinations(all_pairs, 7):
        if is_valid_schedule(schedule):
            schedules.append(schedule)
    return schedules

schedules = generate_schedules(400)[:400]

# print(len(schedules))

prompts = []

for i, schedule in enumerate(schedules):
    if i < 100:
        string = "Generate a response that is slightly indicative of anxiety to each of the following questions."
    elif i < 200:
        string = "Generate a response that is slightly indicative of depression to each of the following questions."
    elif i < 300:
        string = "Generate a response that is slightly indicative of both anxiety and depression to each of the following questions."
    else:
        string = "Generate a neutral response that is indicative of neither anxiety nor depression to each of the following questions."

    string += "\nOutput only your responses to each question, prefixed by the question number."
    random_schedule = random.sample(schedule, k=len(schedule))
    for day, pair in enumerate(random_schedule):
        string += f"\n{day+1}. {pair[0]} {pair[1]}"
    prompts.append(string)

client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.environ["GEMINI_API_KEY"]
)

def query(prompt):
    response = client.chat.completions.create(
        model="gemini-2.0-flash",
        n=1,
        messages=[
            {"role": "system", "content": "You emulate a human who is texting with a digital mental health assistant. Make your responses normal, NOT over the top."},
            {"role": "user", "content": prompt}
        ]
    )
    content = response.choices[0].message.content
    return content

data = []
for i, prompt in enumerate(prompts):
    try:
        response = query(prompt)
    except Exception as e:
        print(f"Waiting due to error: {e}")
        time.sleep(2)

    if i < 100:
        msg_type = "anxiety"
    elif i < 200:
        msg_type = "depression"
    elif i < 300:
        msg_type = "anxiety+depression"
    else:
        msg_type = "neutral"

    data.append({
        "type": msg_type,
        "question": prompt,
        "responses": response
    })
    print(data[len(data)-1])
    time.sleep(1)

with open("responses.json", 'w') as f:
    json.dump(data, f)