import nltk
import sys
import numpy as np
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import joblib

# Load the saved model and vectorizer
model = joblib.load('model.pkl')
vectorizer = joblib.load('vectorizer.pkl')

# Define cleaning function (same as training)
stop_words = set(stopwords.words('english'))

def clean_text(text):
    text = str(text).lower()  # Handle any input type, force to string
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word not in stop_words]
    return ' '.join(tokens)

# new_text = "I'm feeling really stressed rn"
# new_text = "why even is life"
# new_text = "im so tired"
# new_text = "pretty good"
# new_text = "I am feeling the best I have felt in weeks"
# new_text = "happy"
# new_text = "I'm feeling really stressed rn why even is life im so tired lowkey sad"
new_text = sys.argv[1]
new_cleaned = clean_text(new_text)
new_vector = vectorizer.transform([new_cleaned]).toarray()  # Note: transform, not fit_transform

probs = model.predict_proba(new_vector)[0]
prediction = model.classes_[np.argmax(probs)]
print(prediction)

# prediction = model.predict(new_vector)
# print(f"Predicted: {prediction[0]}")

# # Optional: Get probabilities for more nuance
# probs = model.predict_proba(new_vector)[0]
# prob_dict = dict(zip(model.classes_, probs))
# # print(f"Probabilities: {prob_dict}")

# max_prob_class = max(prob_dict, key=prob_dict.get)
# print(f"Predicted: {max_prob_class}")
# # print(f"class with highest probability: {max_prob_class} (probability: {prob_dict[max_prob_class]})")