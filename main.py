import pandas as pd
import re
import nltk
from nltk.corpus import stopwords

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score

# download stopwords (runs once)
nltk.download('stopwords')

# Load dataset
data = pd.read_csv("dataset/phishing_email.csv")

stop_words = set(stopwords.words('english'))

# ---------- Text Cleaning ----------
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^a-zA-Z ]', '', text)
    words = text.split()
    words = [w for w in words if w not in stop_words]
    return " ".join(words)

data['clean_text'] = data['text_combined'].apply(clean_text)

# ---------- Convert Text → Numbers ----------
vectorizer = TfidfVectorizer(max_features=5000)
X = vectorizer.fit_transform(data['clean_text'])

y = data['label']

# ---------- Train/Test Split ----------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ---------- Train Model ----------
model = MultinomialNB()
model.fit(X_train, y_train)

# ---------- Prediction ----------
y_pred = model.predict(X_test)

# ---------- Accuracy ----------
accuracy = accuracy_score(y_test, y_pred)
print("\nModel Accuracy:", accuracy)


import pickle

# save model
pickle.dump(model, open("model.pkl", "wb"))

# save vectorizer
pickle.dump(vectorizer, open("vectorizer.pkl", "wb"))

print("Model saved successfully!")