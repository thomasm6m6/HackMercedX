import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import joblib
from sklearn.svm import SVC

df = pd.read_csv("responses.tsv", sep='\t')
print(df.head())

sequences = df.groupby('user_id').agg({
    "response": lambda x: ' '.join(x),
    "sequence_label": "first"
}).reset_index()

print(sequences.head())

nltk.download('punkt_tab')
nltk.download('punkt')
nltk.download('stopwords')

stop_words = set(stopwords.words("english"))

def clean_text(text):
    text = text.lower()

    text = text.translate(str.maketrans('', '', string.punctuation))

    tokens = word_tokenize(text)

    tokens = [word for word in tokens if word not in stop_words]
    return ' '.join(tokens)

sequences['response']  = sequences['response'].apply(clean_text)
print(sequences['response'].head())

vectorizer = TfidfVectorizer(max_features=500)
X = vectorizer.fit_transform(sequences['response']).toarray()
y = sequences["sequence_label"]

print(X.shape)
print(y.shape)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(X_train.shape, X_test.shape)

model = SVC(kernel='rbf', C=1.0, probability=True)
# model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

train_score = model.score(X_train, y_train)
print(f"Training accuracy: {train_score}")

test_score = model.score(X_test, y_test)
print(f"Test acuracy: {test_score}")

y_pred = model.predict(X_test)
print(list(zip(y_test, y_pred)))

joblib.dump(model, 'model.pkl')
joblib.dump(vectorizer, 'vectorizer.pkl')

new_text = "I'm feeling really stressed rn"
# new_text = "why even is life"
# new_text = "im so tired"
new_cleaned = clean_text(new_text)
new_vector = vectorizer.transform([new_cleaned]).toarray()
prediction = model.predict(new_vector)
print(f"Predicted: {prediction[0]}")

print(sequences['sequence_label'].value_counts())