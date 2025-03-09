import pandas as pd
import nltk
import sys
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import numpy as np
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


model = DistilBertForSequenceClassification.from_pretrained('distilbert_model')
tokenizer = DistilBertTokenizer.from_pretrained('distilbert_model')

new_text = sys.argv[1]
inputs = tokenizer(new_text, return_tensors='pt', truncation=True, padding=True, max_length=1024)
outputs = model(**inputs)
probs = torch.softmax(outputs.logits, dim=1).detach().numpy()[0]
label_map = {0: 'anxiety', 1: 'depression', 2: 'good', 3: 'great'}
prediction = label_map[np.argmax(probs)]
print(prediction)
print(f"Predicted: {prediction}")
print(f"Probabilities: {dict(zip(label_map.values(), probs))}")