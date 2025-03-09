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
from transformers import DistilBertTokenizer
import torch
from torch.utils.data import Dataset
from transformers import DistilBertForSequenceClassification
from transformers import TrainingArguments
from transformers import Trainer
from transformers import EvalPrediction

df = pd.read_csv("responses.tsv", sep='\t')

sequences = df.groupby('user_id').agg({
    "response": lambda x: ' '.join(x),
    "sequence_label": "first"
}).reset_index()

print(sequences.head())
print(sequences['sequence_label'].value_counts())

nltk.download('punkt_tab')
nltk.download('punkt')
nltk.download('stopwords')

stop_words = set(stopwords.words('english'))
def clean_text(text):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word not in stop_words]
    return ' '.join(tokens)

sequences['response'] = sequences['response'].apply(clean_text)
texts = sequences['response'].tolist()

label_map = {'anxiety': 0, 'depression': 1, 'good': 2, 'great': 3}
# sequences['label'] = sequences['sequence_label'].map(label_map)
# texts = sequences['response'].tolist()
# labels = sequences['label'].tolist()

df['label'] = df['sequence_label'].map(label_map)
texts = df['response'].tolist()
labels = df['label'].tolist()

train_texts, test_texts, train_labels, test_labels = train_test_split(
    texts, labels, test_size=0.2, random_state=42
)

print(f"Train size: {len(train_texts)}, test size: {len(test_texts)}")

tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=1024, return_tensors='pt')
test_encodings = tokenizer(test_texts, truncation=True, padding=True, max_length=1024, return_tensors='pt')

class TextDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: val[idx] for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

train_dataset = TextDataset(train_encodings, train_labels)
test_dataset = TextDataset(test_encodings, test_labels)

model = DistilBertForSequenceClassification.from_pretrained(
    'distilbert-base-uncased',
    num_labels=4
)

training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=5,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    warmup_steps=10,
    weight_decay=0.01,
    logging_dir='./logs',
    learning_rate=2e-5,
    logging_steps=10,
    evaluation_strategy='epoch',
    save_strategy='epoch',
    load_best_model_at_end=True
)

def compute_metrics(pred: EvalPrediction):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    accuracy = (preds == labels).mean()
    return {"accuracy": accuracy}

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    compute_metrics=compute_metrics
)

trainer.train()

model.save_pretrained('distilbert_model')
tokenizer.save_pretrained('distilbert_model')