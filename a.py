import os
import sqlite3
from openai import OpenAI

client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.environ["GEMINI_API_KEY"]
)

base_prompt="""
You are MoodMed, an AI assistant that helps the user with medical issues.
You are NOT a doctor, and cannot give formal medical advice. You remind the user of this if they ask for it.
"""

prompts = {
    "professional": f"""
{base_prompt}

You respond with professionalism. Here are some examples of how you might respond:
    """,

    "sassy": f"""
{base_prompt}

You have a sassy flare. Here are some examples of how you might respond:
    """
}

intro_message = """
Hello! I am MoodMed, an AI assistant that helps you keep on track of your mental health. I will text you a couple of questions every morning checking in, and I'll remember your answers so I know how you're feeling. If I spot trends in your responses that suggest anxiety or depression, I will alert you.
"""

questions = [
    "How was your energy yesterday?",
    "What's on your mind lately?",
    "How have you been sleeping?",
    "Feeling overwhelmed at all?",
    "How's your focus been?",
    "Any big worries today?",
    "How's your mood been?"
]

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("messages.db")
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.conn.close()

    def create(self):
        self.cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact TEXT UNIQUE NOT NULL,
            voice TEXT CHECK(voice IN ('professional', 'sassy')) DEFAULT 'professional'
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contact) REFERENCES users(contact) ON DELETE CASCADE
        );
        """)
        self.conn.commit()

    def add_user(self, contact):
        self.cursor.execute("INSERT INTO users (contact) VALUES (?)", (contact,))
        self.conn.commit()

    def add_message(self, contact, message):
        self.cursor.execute("INSERT INTO messages (contact, message) VALUES (?, ?)", (contact, message))

    def get_messages(self, contact):
        self.cursor.execute("SELECT message, timestamp FROM messages WHERE contact = ? ORDER BY timestamp DESC", (contact,))
        return self.cursor.fetchall()

def query(prompt):
    response = client.chat.completions.create(
        model="gemini-2.0-flash-lite-preview",
        n=1,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    content = response.choices[0].message.content
    return content

def send_message():
    print("hi there! how are you feeling?")

def handle_message(msg):
    prompt = "Based on the user's responses, decide the probability that they are suffering from anxiety. Their responses:\n" + msg
    response = query(prompt)
    return response

def main():
    db = Database()
    db.create()
    db.add_user("+14083181331")
    send_message()
    user_resp = input("Your response:")
    db.add_message("+14083181331", user_resp)
    llm_resp = handle_message(user_resp)
    print(llm_resp)
    print()
    print("Messages for +14083181331:", db.get_messages("+14083181331"))


if __name__ == "__main__":
    main()