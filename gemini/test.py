import os
import sys
import time
from openai import OpenAI

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

while True:
    try:
        result = query(f"""
        Decide whether the following message is indicative of anxiety, depression, or good mental health. Return only one word, "anxiety", "depression", or "good".

        {sys.argv[1]}
        """)
        break
    except Exception as e:
        print(f"running again, error: {e}", file=sys.stderr)
        time.sleep(1)

print(result.strip())