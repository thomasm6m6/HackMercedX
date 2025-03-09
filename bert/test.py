import sys
import numpy as np
from transformers import DistilBertTokenizer
import torch
from transformers import DistilBertForSequenceClassification


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