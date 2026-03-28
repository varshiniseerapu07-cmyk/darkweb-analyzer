from flask import Flask, render_template, request, redirect, url_for
import pickle
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np
import requests
from bs4 import BeautifulSoup
import re  # for text cleaning

app = Flask(__name__)

# 🔹 Load model and tokenizer
model = load_model("model.keras")
with open("tokenizer.pkl", "rb") as f:
    tokenizer = pickle.load(f)

MAX_LEN = 150  # match predict_text
le = pickle.load(open("label_encoder.pkl", "rb"))  # your label encoder

# 🔹 Define your clean_text function here
def clean_text(text):
    text = text.lower()
    text = re.sub(r"http\S+", "", text)  # remove URLs
    text = re.sub(r"[^a-z0-9\s]", "", text)  # remove punctuation
    text = re.sub(r"\s+", " ", text).strip()  # remove extra spaces
    return text

# 🔹 Your prediction function
def predict_text(data):

    def get_text_from_url(url):
        try:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")
            for script in soup(["script","style"]):
                script.extract()
            return soup.get_text(separator=" ").strip()
        except:
            return ""

    user_text = data.get('text',"")
    url = data.get('url',"")
    url_content = get_text_from_url(url) if url else ""

    if user_text and url_content:
        input_text = user_text + " " + url_content
    elif user_text:
        input_text = user_text
    elif url_content:
        input_text = url_content
    else:
        input_text = url  # fallback

    combined_text = f"{data['source_ip']} {data['dest_ip']} {data['protocol']} {data['packet_type']} {data['packet_size']} {input_text}"
    cleaned = clean_text(combined_text)

    # ML model prediction
    seq = tokenizer.texts_to_sequences([cleaned])
    padded = pad_sequences(seq, maxlen=MAX_LEN)
    pred = model.predict(padded)
    category = le.inverse_transform([np.argmax(pred)])[0]
    confidence = float(np.max(pred)) * 100

    text_lower = combined_text.lower()

    # ✅ Keyword mapping
    safe_keywords = [
      "learn", "learning", "course", "tutorial",
    "education", "ethical", "training",
    "practice", "cybersecurity", "research",
    
    # Additional educational / safe terms
    "study", "lecture", "workshop", "seminar",
    "class", "lecture notes", "online course",
    "guide", "manual", "document", "documentation",
    "programming", "coding", "development",
    "safe", "security awareness", "ethical hacking",
    "information security", "network security",
    "data science", "machine learning", "ai", "artificial intelligence",
    "analytics", "technology", "computer science",
    "tutorials", "tips", "training material", "hands-on",
    "practice lab", "demo", "learning resources", "knowledge",
    "skill development", "experiment", "simulation"
        ]
    danger_map = {
         "organ": "illegal", 
    "organs": "illegal", 
    "kidney": "illegal",
    "liver": "illegal",
    "heart": "illegal",
    "human trafficking": "human_trafficking",
    "trafficking": "human_trafficking",

    # Hacking & cybercrime
    "hack": "hacking", 
    "hack account": "hacking", 
    "steal password": "hacking",
    "crack password": "hacking", 
    "bank hack": "hacking",
    "phishing": "hacking",
    "malware": "hacking",
    "ransomware": "hacking",
    "exploit": "hacking",
    "ddos": "hacking",

    # Drugs
    "drug": "drug", 
    "cocaine": "drug", 
    "heroin": "drug",
    "meth": "drug",
    "marijuana": "drug",
    "ecstasy": "drug",
    "lsd": "drug",
    "fentanyl": "drug",

    # Fraud & financial crimes
    "fraud": "fraud", 
    "scam": "scam",
    "credit card": "carding", 
    "carding": "carding",
    "identity theft": "fraud",

    # Weapons & illegal items
    "weapon": "weapons", 
    "gun": "weapons",
    "firearm": "weapons",
    "knife": "weapons",
    "explosive": "weapons",
    "bomb": "weapons",

    # Dark web activity (illegal only)
    "darkweb": "darknet_activity",
    "onion market": "darknet_activity",
    "dnm": "darknet_activity",  # darknet market
    "cryptomarket": "darknet_activity",

    # Misc illegal / adult content
    "child abuse": "illegal",
    "child porn": "illegal",
    "abuse material": "illegal",
    "extremist": "illegal",
    "terrorist": "illegal",
    "hitman": "illegal",
    "assassination": "illegal",
    }

    detected = False
    for key, value in danger_map.items():
        if key in text_lower:
            category = value
            threat = "Threat Found"
            detected = True
            break

    if not detected:
        if any(word in text_lower for word in safe_keywords):
            category = "educational"
            threat = "Safe"
        else:
            category = "normal"
            threat = "Safe"

    return category, round(confidence, 2), threat

# 🏠 Home
@app.route("/")
def intro():
    return render_template("intro.html")

# 📥 Main page
@app.route("/main")
def main():
    return render_template("main.html")

# ⚡ Analyze POST
@app.route("/analyze", methods=["POST"])
def analyze():
    data = {
        "source_ip": request.form.get("source_ip", ""),
        "dest_ip": request.form.get("dest_ip", ""),
        "protocol": request.form.get("protocol", ""),
        "packet_type": request.form.get("packet_type", ""),
        "packet_size": request.form.get("packet_size", ""),
        "text": request.form.get("text", ""),
        "url": request.form.get("url", "")
    }

    category, confidence, threat = predict_text(data)

    # 🔹 Pass to loading page
    return redirect(url_for(
        "loading",
        category=category,
        confidence=confidence,
        threat=threat
    ))

# ⏳ Loading page
@app.route("/loading")
def loading():
    category = request.args.get("category")
    confidence = request.args.get("confidence")
    threat = request.args.get("threat")
    return render_template("analyze.html",
                           category=category,
                           confidence=confidence,
                           threat=threat)

# 🎯 Result page
@app.route("/result")
def result():
    category = request.args.get("category")
    confidence = request.args.get("confidence")
    threat = request.args.get("threat")
    return render_template("result.html",
                           category=category,
                           confidence=confidence,
                           threat=threat)

# 🚀 Run server
if __name__ == "__main__":
    app.run(debug=True)