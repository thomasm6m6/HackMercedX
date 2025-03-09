import os
import ssl
import sys
import time
import random
import sqlite3
import re
import threading
import base64
from email.message import EmailMessage
from queue import Queue
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI
from flask import Flask, render_template_string
import numpy as np
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import torch

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

# Flask app setup
app = Flask(__name__)

# HTML template for the "Next" button page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>MoodMed Check-in</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-color: #f0f0f0; }
        button { padding: 20px 40px; font-size: 24px; background-color: #4CAF50; color: white; border: none; border-radius: 10px; cursor: pointer; }
        button:hover { background-color: #45a049; }
    </style>
</head>
<body>
    <button onclick="fetch('/trigger_checkin').then(() => {e=document.querySelector('#status'); e.innerHTML = e.innerHTML + '<br>Updated!'})">Next</button>
    <p id='status'></p>
</body>
</html>
"""

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("messages.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self.create()

    def create(self):
        with self.lock:
            self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact TEXT UNIQUE NOT NULL,
                gv_email TEXT NOT NULL,
                voice TEXT CHECK(voice IN ('professional', 'sassy')) DEFAULT 'professional',
                last_interaction DATETIME,
                subscribed BOOLEAN DEFAULT 1,
                mood_streak INTEGER DEFAULT 0,
                streak_type TEXT CHECK(streak_type IN ('anxiety', 'depression', 'great', NULL)),
                previous_questions TEXT
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact TEXT NOT NULL,
                message1 TEXT NOT NULL,
                response TEXT,
                message2 TEXT,
                mood_analysis TEXT CHECK(mood_analysis IN ('anxiety', 'depression', 'great', NULL)),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact) REFERENCES users(contact) ON DELETE CASCADE
            );
            """)
            self.conn.commit()

    def add_user(self, contact, gv_email):
        with self.lock:
            try:
                self.conn.execute(
                    "INSERT INTO users (contact, gv_email, last_interaction, subscribed) VALUES (?, ?, ?, 1)",
                    (contact, gv_email, datetime.now())
                )
                self.conn.commit()
                return True
            except sqlite3.IntegrityError:
                # User already exists, ensure they're marked as subscribed
                self.conn.execute(
                    "UPDATE users SET subscribed = 1, last_interaction = ? WHERE contact = ?",
                    (datetime.now(), contact)
                )
                self.conn.commit()
                return False

    def update_user(self, contact, voice=None, subscribed=None):
        with self.lock:
            updates = ["last_interaction = ?"]
            params = [datetime.now()]

            if voice:
                updates.append("voice = ?")
                params.append(voice)

            if subscribed is not None:
                updates.append("subscribed = ?")
                params.append(1 if subscribed else 0)

            if updates:
                query = f"UPDATE users SET {', '.join(updates)} WHERE contact = ?"
                params.append(contact)
                self.conn.execute(query, params)
                self.conn.commit()

    def add_message(self, contact, message1, response=None, message2=None, mood_analysis=None):
        with open("/tmp/a.log", 'w') as f:
            print(f"adding the message... contact={contact}, message1={message1}, response={response}, message2={message2}, mood_analysis={mood_analysis}", file=f, flush=True)
        with self.lock:
            self.conn.execute(
                "INSERT INTO messages (contact, message1, response, message2, mood_analysis) VALUES (?, ?, ?, ?, ?)",
                (contact, message1, response, message2, mood_analysis)
            )
            self.conn.commit()

            # Update user's mood streak if mood analysis is provided
            if mood_analysis:
                self.update_mood_streak(contact, mood_analysis)

    def update_mood_streak(self, contact, current_mood):
        with self.lock:
            user = self.get_user(contact)
            if not user:
                return

            previous_streak = user['mood_streak']
            previous_type = user['streak_type']

            # Reset streak if mood type changes or if it's "great"
            if current_mood == 'great':
                self.conn.execute(
                    "UPDATE users SET mood_streak = 0, streak_type = ? WHERE contact = ?",
                    (current_mood, contact)
                )
            elif previous_type == current_mood:
                # Increment the streak if the same negative mood continues
                self.conn.execute(
                    "UPDATE users SET mood_streak = mood_streak + 1 WHERE contact = ?",
                    (contact,)
                )
            else:
                # Start a new streak with the current negative mood
                self.conn.execute(
                    "UPDATE users SET mood_streak = 1, streak_type = ? WHERE contact = ?",
                    (current_mood, contact)
                )

            self.conn.commit()

    def get_user(self, contact):
        with self.lock:
            cursor = self.conn.execute("SELECT * FROM users WHERE contact = ?", (contact,))
            return cursor.fetchone()

    def get_all_subscribed_users(self):
        with self.lock:
            cursor = self.conn.execute("SELECT * FROM users WHERE subscribed = 1")
            return cursor.fetchall()

    def get_recent_messages(self, contact, days=2):
        with self.lock:
            cursor = self.conn.execute(
                "SELECT message1, message2, mood_analysis, timestamp FROM messages WHERE contact = ? AND timestamp > ? ORDER BY timestamp DESC",
                (contact, datetime.now() - timedelta(days=days))
            )
            return cursor.fetchall()

class EmailService:
    def __init__(self):
        self.creds = self.authenticate_gmail()
        self.service = build('gmail', 'v1', credentials=self.creds)
        self.send_queue = Queue()
        self.processed_messages = set()
        self.lock = threading.Lock()

        self.send_thread = threading.Thread(target=self._process_send_queue, daemon=True)
        self.send_thread.start()

    def authenticate_gmail(self):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds

    def send_message(self, to, subject, text):
        print(text, end='\n!\n', file=sys.stderr)
        message = EmailMessage()
        message.set_content(text)
        message["To"] = to
        message["From"] = "me"
        message["Subject"] = subject
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        self.send_queue.put({"raw": encoded_message})

    def _process_send_queue(self):
        while True:
            print("_process_send_queue")
            message = self.send_queue.get()
            try:
                with self.lock:
                    while True:
                        try:
                            self.service.users().messages().send(userId="me", body=message).execute()
                            break
                        except ssl.SSLError as ssl_error:
                            print(f"SSL Error: {ssl_error}")
                            time.sleep(0.1)
            except HttpError as error:
                print(f"Error sending message: {error}")
            finally:
                self.send_queue.task_done()

    def poll_emails(self, db, ai_service):
        while True:
            print("poll_emails")
            try:
                results = self.service.users().messages().list(userId='me', maxResults=5).execute()
                messages = results.get('messages', [])
                if not messages:
                    print("No messages found.")
                    time.sleep(1)
                    continue

                for message in messages:
                    try:
                        msg_id = message.get('id', 'unknown')
                        print(f"Processing message {msg_id}")
                        with self.lock:
                            if msg_id in self.processed_messages:
                                print(f"Message {msg_id} already processed, skipping.")
                                continue
                            msg = self.service.users().messages().get(userId='me', id=msg_id).execute()
                            if not msg:
                                print(f"Failed to retrieve message {msg_id}")
                                continue
                            self.processed_messages.add(msg_id)

                        # Check payload existence
                        if 'payload' not in msg:
                            print(f"Message {msg_id} has no payload")
                            continue
                        if 'headers' not in msg['payload']:
                            print(f"Message {msg_id} has no headers in payload")
                            continue

                        # Safer header access
                        from_header = None
                        for header in msg['payload']['headers']:
                            if header['name'].lower() == 'from':
                                from_header = header['value']
                                break

                        if not from_header:
                            print(f"No 'From' header found in message {msg_id}")
                            continue

                        sender = extract_name_and_email(from_header)
                        if not sender['email']:
                            print(f"Could not extract email from header in message {msg_id}")
                            continue

                        if (sender['email'].endswith("@txt.voice.google.com") and
                                'parts' in msg['payload']):
                            contact = sender['contact'] or "Unknown Contact"  # Fallback if contact is None
                            email = sender['email']
                            is_new_user = db.add_user(contact, email)

                            for part in msg['payload']['parts']:
                                if part.get('mimeType') == "text/plain":
                                    if 'body' not in part or 'data' not in part['body']:
                                        print(f"Message {msg_id} part has no body/data")
                                        continue
                                    encoded_data = part['body']['data']
                                    if not encoded_data:
                                        print(f"Message {msg_id} has empty body data")
                                        continue
                                    text = base64.urlsafe_b64decode(encoded_data).decode('utf-8')
                                    text = '\n'.join(text.split('\n')[2:-11])

                                    if is_new_user:
                                        print(f"Handling new user for message {msg_id}")
                                        ai_service.handle_new_user(contact, db, self)
                                    else:
                                        print(f"Handling user response for message {msg_id}")
                                        ai_service.handle_user_response(contact, text, db, self)

                    except Exception as inner_error:
                        print(f"Error processing individual message {msg_id}: {inner_error}")
                        continue
            except Exception as e:
                print(f"Error polling emails: {e}")
            finally:
                print("cycle completed, sleeping")
                time.sleep(1)

    # def poll_emails(self, db, ai_service):
    #     while True:
    #         print("poll_emails")
    #         try:
    #             results = self.service.users().messages().list(userId='me', maxResults=5).execute()
    #             messages = results.get('messages', [])

    #             for message in messages:
    #                 try:
    #                     print("a")
    #                     with self.lock:
    #                         if message['id'] in self.processed_messages:
    #                             continue
    #                         msg = self.service.users().messages().get(userId='me', id=message['id']).execute()
    #                         self.processed_messages.add(message['id'])

    #                     print("b")
    #                     # Safer header access
    #                     from_header = None
    #                     for header in msg['payload']['headers']:
    #                         if header['name'].lower() == 'from':
    #                             from_header = header['value']
    #                             break

    #                     print("c")
    #                     if not from_header:
    #                         print(f"No 'From' header found in message {message['id']}")
    #                         continue

    #                     sender = extract_name_and_email(from_header)

    #                     print("d")
    #                     if (sender['email'] and sender['email'].endswith("@txt.voice.google.com") and
    #                             'parts' in msg['payload']):
    #                         contact = sender['contact']
    #                         email = sender['email']
    #                         is_new_user = db.add_user(contact, email)

    #                         print("d.1")
    #                         for part in msg['payload']['parts']:
    #                             print("d.2")
    #                             if part['mimeType'] == "text/plain":
    #                                 text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
    #                                 text = '\n'.join(text.split('\n')[2:-11])

    #                                 # Handle initial message differently for new users
    #                                 if is_new_user:
    #                                     print("d.3")
    #                                     ai_service.handle_new_user(contact, db, self)
    #                                 else:
    #                                     print("d.4")
    #                                     ai_service.handle_user_response(contact, text, db, self)

    #                     print("e")
    #                 except Exception as inner_error:
    #                     print(f"Error processing individual message {message.get('id', 'unknown')}: {inner_error}")
    #                     continue
    #         except Exception as e:
    #             print(f"Error polling emails: {e}")
    #         finally:
    #             print("cycle completed, sleeping")
    #             time.sleep(1)

def extract_name_and_email(from_header):
    pattern = r'(?:"?([^"]*)"?\s*)?(?:<)?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:>)?'
    match = re.match(pattern, from_header.strip("From: ").strip())
    return {
        'contact': match.group(1).strip() if match and match.group(1) else None,
        'email': match.group(2) if match else None
    }

class AIService:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=os.environ["GEMINI_API_KEY"]
        )
        self.model = DistilBertForSequenceClassification.from_pretrained('distilbert_model')
        self.tokenizer = DistilBertTokenizer.from_pretrained('distilbert_model')
        self.default_system_prompt = """
        You are MoodMed, an AI assistant that helps the user with medical issues.
        You are NOT a doctor, and cannot give formal medical advice.
        You respond ONLY on one line, and never with markdown formatting.
        """
        self.questions = [
            "How was your energy yesterday?",
            "What's on your mind lately?",
            "How have you been sleeping?",
            "Feeling overwhelmed at all?",
            "How's your focus been?",
            "Any big worries today?",
            "How's your mood been?"
        ]
        self.intro_message = """
        Hello! I am MoodMed, an AI assistant that helps you keep track of your mental health.
        I will text you a couple of questions every morning checking in, and I'll remember how you're feeling.
        If I spot trends in your responses that suggest anxiety or depression, I will alert you.
        Note: You can change the way I write! Tell me to "enable sassy mode"... if you dare ;) Reply with 'START' to begin your daily check-ins.
        """

        # Define concerned responses based on streak length
        self.concern_levels = {
            'anxiety': {
                1: "I notice you've been feeling anxious today. Remember to take some deep breaths when you feel overwhelmed.",
                2: "You've been anxious for a couple days now. Have you tried any mindfulness exercises?",
                3: "I'm noticing a pattern of anxiety over the past few days. Consider talking to someone you trust about what's on your mind.",
                5: "You've been anxious for 5 days straight now. This might be a good time to check in with a healthcare professional.",
                7: "I'm quite concerned about your anxiety levels over the past week. Please consider reaching out to a mental health professional."
            },
            'depression': {
                1: "I sense you're feeling a bit down today. Try to do one small thing that brings you joy.",
                2: "You've been feeling down for a couple days. Remember to be gentle with yourself.",
                3: "I've noticed you've been down for several days now. Have you been getting outside at all?",
                5: "You've been showing signs of depression for 5 days straight. It might help to talk to someone about what you're experiencing.",
                7: "I'm really concerned about your mood over the past week. Please consider talking to a healthcare provider about how you're feeling."
            }
        }

    def query(self, user_prompt, system_prompt=""):
        system_prompt = system_prompt or self.default_system_prompt
        for _ in range(3):
            try:
                response = self.client.chat.completions.create(
                    model="gemini-2.0-flash",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"AI query error: {e}")
                time.sleep(1)
        return "Sorry, I'm having trouble responding right now."

    def analyze_response(self, text):
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=1024)
        outputs = self.model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1).detach().numpy()[0]
        label_map = {0: 'anxiety', 1: 'depression', 2: 'good', 3: 'great'}
        prediction = label_map[np.argmax(probs)]
        return prediction

    def handle_new_user(self, contact, db, email_service):
        user = db.get_user(contact)
        if not user:
            return

        # Send intro message
        db.add_message(contact, self.intro_message, None)
        email_service.send_message(user['gv_email'], "MoodMed", self.intro_message)

    def send_daily_checkin(self, contact, db, email_service):
        user = db.get_user(contact)
        if not user or not user['subscribed']:
            return

        voice = "super sassy" if user['voice'] == "sassy" else "friendly and respectful"
        recent_msgs = db.get_recent_messages(contact)
        yesterday = recent_msgs[0]['message2'] if recent_msgs and recent_msgs[0]['message2'] else "(no message yesterday)"
        two_days = recent_msgs[1]['message2'] if len(recent_msgs) > 1 and recent_msgs[1]['message2'] else "(no message 2 days ago)"

        previous_qs = user['previous_questions'].split(',') if user['previous_questions'] else []
        available_qs = [q for q in self.questions if q not in previous_qs]
        if len(available_qs) < 2:
            available_qs = self.questions
        qs = random.sample(available_qs, 2)

        db.conn.execute(
            "UPDATE users SET previous_questions = ? WHERE contact = ?",
            (','.join(qs), contact)
        )
        db.conn.commit()

        prompt = f"""
        Generate a message greeting the user and asking these two daily morning check-in questions. Be {voice}.
        1. {qs[0]}
        2. {qs[1]}
        Previous messages:
        --- YESTERDAY ---
        {yesterday}
        --- 2 DAYS AGO ---
        {two_days}
        """
        message = self.query(prompt)
        # db.add_message(contact, message, None)
        email_service.send_message(user['gv_email'], "MoodMed", message)

    def get_concern_response(self, mood_type, streak_count):
        # Find the appropriate concern level based on streak length
        if streak_count == 0:
            streak_count = 1
        levels = sorted([k for k in self.concern_levels[mood_type].keys() if k <= streak_count], reverse=True)
        if levels:
            return self.concern_levels[mood_type][levels[0]]
        return None  # Should never happen since we have level 1 defined

    def handle_user_response(self, contact, text, db, email_service):
        print("handle_user_response 0")
        user = db.get_user(contact)
        voice = "super sassy" if user['voice'] == "sassy" else "friendly and respectful"
        if not user:
            return

        # Check for special commands
        text_lower = text.lower().strip()

        print("handle_user_response 1")
        # Subscription management
        if text_lower in ["unsubscribe", "stop"]:
            db.update_user(contact, subscribed=False)
            response = "You've been unsubscribed. Text 'START' anytime to restart!"
            email_service.send_message(user['gv_email'], "MoodMed", response)
            return
        elif text_lower in ["start", "subscribe"]:
            db.update_user(contact, subscribed=True)
            prompt = f"Generate a message informing the user they are now subscribed to daily check-ins, and you will check in with them tomorrow morning. Be {voice}."
            response = self.query(prompt)
            email_service.send_message(user['gv_email'], "MoodMed", response)
            return

        # Voice mode commands
        elif "enable sassy mode" in text_lower:
            db.update_user(contact, voice="sassy")
            response = "Sassy mode activated! Get ready for some attitude."
            email_service.send_message(user['gv_email'], "MoodMed", response)
            return
        elif "disable sassy mode" in text_lower:
            db.update_user(contact, voice="professional")
            response = "Sassy mode deactivated. Back to professional mode."
            email_service.send_message(user['gv_email'], "MoodMed", response)
            return

        print("handle_user_response 2")
        # Analyze message mood and update database
        mood = self.analyze_response(text)
        print("handle_user_response 2.1")

        # Get last message to find what we need to respond to
        recent_msgs = db.get_recent_messages(contact, days=1)
        print("handle_user_response 2.2")
        last_message = recent_msgs[0] if recent_msgs else None

        print("handle_user_response 3")
        # Generate appropriate response based on mood streak
        if mood in ['anxiety', 'depression']:
            print("anxiety/depression")
            # Store the message and update streak before generating response
            # db.add_message(contact, "", text, None, mood)
            print("added anxiety/depression message...")

            # Get updated user data with the new streak information
            print("getting user...")
            user = db.get_user(contact)
            streak_count = user['mood_streak']
            print("Got user...")

            # Get response based on streak length
            print("getting concern response...")
            response = self.get_concern_response(mood, streak_count)
            print("Got concern response..")
        else:  # great mood
            print("great")
            voice = "super sassy" if user['voice'] == "sassy" else "friendly and respectful"
            prompt = f"""
            The user seems to be doing well today. Create a {voice} response that's upbeat and encouraging.
            Keep it short and natural, under 2 sentences.

            User message: {text}
            """
            response = self.query(prompt)
            print("adding the great message...")
            # db.add_message(contact, "", text, response, mood)
            print("handle_user_response 5")

        print("HERE", "response:", response)
        email_service.send_message(user['gv_email'], "MoodMed", response)

        # Update the message with the response
        with db.lock:
            db.conn.execute(
                "UPDATE messages SET response = ? WHERE contact = ? ORDER BY id DESC LIMIT 1",
                (response, contact)
            )
            db.conn.commit()

def main():
    db = Database()
    email_service = EmailService()
    ai_service = AIService()

    poll_thread = threading.Thread(
        target=email_service.poll_emails,
        args=(db, ai_service),
        daemon=True
    )
    poll_thread.start()

    @app.route('/')
    def index():
        return render_template_string(HTML_TEMPLATE)

    @app.route('/trigger_checkin')
    def trigger_checkin():
        for user in db.get_all_subscribed_users():
            ai_service.send_daily_checkin(user['contact'], db, email_service)
        return "Check-in triggered!"

    # Run Flask in a separate thread
    def run_flask():
        app.run(host='0.0.0.0', port=5001, debug=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    def daily_checkin():
        while True:
            now = datetime.now()
            if now.hour == 8:
                for user in db.get_all_subscribed_users():
                    ai_service.send_daily_checkin(user['contact'], db, email_service)
            time.sleep(3600)

    checkin_thread = threading.Thread(target=daily_checkin, daemon=True)
    checkin_thread.start()

    try:
        poll_thread.join()
        checkin_thread.join()
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    main()