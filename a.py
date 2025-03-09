import os
import sys
import time
import random
import sqlite3
import re
import threading
import base64
from email.message import EmailMessage
from email.mime.text import MIMEText

from openai import OpenAI
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# TODO: initialize database, load model into memory
# TODO: gemini prompts
# TODO: use push api for gmail

# Scopes define the level of access (read-only in this case)
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

def authenticate_gmail():
    creds = None
    # Check if token.json exists (stores the user's access and refresh tokens)
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials, prompt the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def extract_email_from_header(from_header):
    # Pattern: Matches an email address between < > or standalone
    email_pattern = r'(?:<)?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:>)?'
    match = re.search(email_pattern, from_header)
    if match:
        return match.group(1)  # Group 1 is the email address without < >
    return None

def extract_name_and_email(from_header):
    # Pattern: Captures optional name (quoted or unquoted) and email
    pattern = r'(?:"?([^"]*)"?\s*)?(?:<)?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:>)?'
    match = re.match(pattern, from_header.strip("From: ").strip())

    if match:
        name = match.group(1)  # Display name (might be None if not present)
        email = match.group(2)  # Email address
        return {'name': name.strip() if name else None, 'email': email}
    return {'name': None, 'email': None}

def create_message(to, subject, message_text, sender="me"):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

def send_message(service, message):
    try:
        sent_message = service.users().messages().send(userId='me', body=message).execute()
        print(f"Message sent, id: {sent_message['id']}")
        return sent_message
    except Exception as error:
        print(f"Error: {error}")
        return None

def send_message2(to, subject, message_text):
    try:
        message = EmailMessage()
        message.set_content(message_text)
        message["To"] = to
        message["From"] = "me"
        message["Subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        print(f"Message id: {send_message["id"]}")
    except HttpError as error:
        print(f"An error occurred: {error}")
        send_message = None
    return send_message

def send(to, text):
    # msg = create_message(to, "MoodMed SMS", text)
    # send_message(service, msg)
    send_message2(to, "MoodMed SMS", text)

# Authenticate and get emails
creds = authenticate_gmail()
service = build('gmail', 'v1', credentials=creds)

# get_emails()
# send("14086342733.14083181331.G6t2NKtTdt@txt.voice.google.com", "hi there")

def poll_emails():
    while True:
        results = service.users().messages().list(userId='me', maxResults=5).execute()
        messages = results.get('messages', [])
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            headers = msg['payload']['headers']
            from_header = next(header['value'] for header in headers if header['name'] == 'From')

            sender = extract_name_and_email(from_header)
            from_number = sender['name']
            from_email = sender['email']
            if from_number is not None and from_email is not None \
                    and from_email.endswith("@txt.voice.google.com") and "parts" in msg['payload']:
                print(from_number, from_email)
                db.add_user(from_number, from_email)
                for part in msg['payload']['parts']:
                    if part['mimeType'] == "text/plain":
                        data = part['body']['data']
                        text = base64.urlsafe_b64decode(data).decode('utf-8')
                        print('\n'.join(text.split('\n')[2:-11]), end='\n\n')
        time.sleep(0.5)

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
            gv_email TEXT NOT NULL,
            voice TEXT CHECK(voice IN ('professional', 'sassy')) DEFAULT 'professional'
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact TEXT NOT NULL,
            message1 TEXT NOT NULL,
            response TEXT NOT NULL,
            message2 TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contact) REFERENCES users(contact) ON DELETE CASCADE
        );
        """)
        self.conn.commit()

    def add_user(self, contact, gv_email):
        self.cursor.execute("INSERT INTO users (contact, gv_email) VALUES (?, ?)", (contact, gv_email))
        self.conn.commit()

    def add_message(self, contact, message):
        self.cursor.execute("INSERT INTO messages (contact, message) VALUES (?, ?)", (contact, message))

    def get_messages(self, contact):
        self.cursor.execute("SELECT message, timestamp FROM messages WHERE contact = ? ORDER BY timestamp DESC", (contact,))
        return self.cursor.fetchall()

def send_message():
    print("hi there! how are you feeling?")

def handle_message(msg):
    prompt = "Based on the user's responses, decide the probability that they are suffering from anxiety. Their responses:\n" + msg
    response = query(prompt)
    return response

client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.environ["GEMINI_API_KEY"]
)

# TODO store in db
sassy = True

default_system_prompt="""
You are MoodMed, an AI assistant that helps the user with medical issues.
You are NOT a doctor, and cannot give formal medical advice. You remind the user of this if asked for it.
The user already knows both of those, you do not repeat them unless directly asked.
You do not use emojis or markdown formatting in your responses.
"""

def query(user_prompt, system_prompt=""):
    if system_prompt == "":
        system_prompt = default_system_prompt
    while True:
        try:
            response = client.chat.completions.create(
                model="gemini-2.0-flash-lite-preview",
                n=1,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            content = response.choices[0].message.content
            return content
        except Exception as e:
            print("Error, trying again: {e}", file=sys.stderr)
            time.sleep(1)

# TODO I'm thinking maybe suggest a particular existing style for it to adopt for sassy, e.g. punk teenager or something
# give it a stereotypical character to play basically
prompts = {
    "professional": f"""
You respond with professionalism. Here are some examples of how you might respond:
    """,

    "sassy": f"""
You have a sassy flare. Here are some examples of how you might respond:
    """
}

intro_message = """
Hello! I am MoodMed, an AI assistant that helps you keep on track of your mental health. I will text you a couple of questions every morning checking in, and I'll remember how you're feeling. If I spot trends in your responses that suggest anxiety or depression, I will alert you.

Note: You can change the way I write! Tell me to enable "sassy mode"... if you dare ;)

What would you like me to call you?
"""

daily_prompt_template = """
Generate a message greeting the user and asking them the following two daily morning check-in questions. Be {}.
Do not attempt to hold a conversation with the user; you can if they want, but you should only expect one response from them.
The user is expecting these questions, so you do not need to explain that. You may vary the language of the questions.
1. {}
2. {}

The messages you sent the last two days follows, for you to avoid repeating the same wording:

--- BEGIN MESSAGE FROM YESTERDAY ---
{}
--- END MESSAGE FROM YESTERDAY ---

--- BEGIN MESSAGE FROM 2 DAYS AGO ---
{}
-- END MESSAGE FROM 2 DAYS AGO ---
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

def get_daily_message():
    qs = random.sample(questions, 2)
    prompt = daily_prompt_template.format(
        "super sassy" if sassy else "friendly and respectful",
        qs[0], qs[1], "(no message yesterday)", "(no message 2 days ago)"
    )
    return query(prompt)

db = Database()
db.create()

thread = threading.Thread(target=poll_emails)
thread.start()

    # db.add_user("+14083181331")
    # send_message()
    # user_resp = input("Your response:")
    # db.add_message("+14083181331", user_resp)
    # llm_resp = handle_message(user_resp)
    # print(llm_resp)
    # print()
    # print("Messages for +14083181331:", db.get_messages("+14083181331"))

print(intro_message)
for i in range(10):
    print(get_daily_message())
    print()


"""
flow:
- user texts the number
- user is added to database
- LLM responds:
  - welcomes user (with the context of the user's initial message, to respond to it if appropriate)
  - informs them that they've been subscribed and can send a message requesting to unsubscribe at any time
- I press a button, triggering a new "day", the LLM sends a message asking two of the 7 questions
- if user does not respond in several hours, send a reminder
- once user responds, analyze response to decide if it signals anxiety/depression
- add message and analysis to database
- send a message back to the user
  - if no anxiety/depression, just something like "have a nice day!"
  - if anxiety/depression, point this out, maybe subtly e.g. "make sure to get some rest"
  - if anxiety/depression for several days in a row, suggest seeking care
"""