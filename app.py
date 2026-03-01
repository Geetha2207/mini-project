from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import os
from datetime import datetime
from PyPDF2 import PdfReader

# --------------------------------
# APP CONFIG
# --------------------------------
app = Flask(__name__)
app.secret_key = "supersecretkey"

# --------------------------------
# LOAD AI MODEL
# --------------------------------
model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# store history temporarily
history = []

# --------------------------------
# LOGIN PAGE
# --------------------------------
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["user"] = username
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid Login")

    return render_template("login.html")


# --------------------------------
# HOME PAGE
# --------------------------------
@app.route("/home")
def home():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("index.html")


# --------------------------------
# EMAIL TEXT PREDICTION
# --------------------------------
@app.route("/analyze", methods=["POST"])
def analyze():

    if "user" not in session:
        return redirect(url_for("login"))

    text = ""

    # ---- TEXT INPUT ----
    email_text = request.form.get("email")

    if email_text:
        text += email_text + " "

    # ---- FILE INPUT ----
    file = request.files.get("file")

    if file and file.filename != "":

        if file.filename.endswith(".txt"):
            text += file.read().decode("utf-8")

        elif file.filename.endswith(".pdf"):
            reader = PdfReader(file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted

    # ---- EMPTY CHECK ----
    if text.strip() == "":
        return render_template(
            "index.html",
            prediction="⚠️ Please enter text or upload file"
        )

    # ---- AI PREDICTION ----
    vector = vectorizer.transform([text])
    prediction = model.predict(vector)[0]
    probability = model.predict_proba(vector)[0]

    phishing_prob = probability[1] * 100
    safe_prob = probability[0] * 100

    result = "🚨 Phishing Email" if prediction == 1 else "✅ Safe Email"

    history.append({
        "text": text[:50],
        "result": result,
        "risk": round(phishing_prob, 2),
        "time": datetime.now().strftime("%H:%M:%S")
    })

    return render_template(
        "index.html",
        prediction=result,
        risk=round(phishing_prob, 2),
        safe=round(safe_prob, 2)
    )

# --------------------------------
# FILE UPLOAD (PDF / TXT)
# --------------------------------
@app.route("/upload", methods=["POST"])
def upload():

    if "user" not in session:
        return redirect(url_for("login"))

    if "file" not in request.files:
        return render_template("index.html",
                               prediction="No file selected")

    file = request.files["file"]

    if file.filename == "":
        return render_template("index.html",
                               prediction="No file selected")

    text = ""

    # TXT FILE
    if file.filename.lower().endswith(".txt"):
        text = file.read().decode("utf-8", errors="ignore")

    # PDF FILE
    elif file.filename.lower().endswith(".pdf"):
        reader = PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

    else:
        return render_template("index.html",
                               prediction="Unsupported file")

    # ✅ CHECK EMPTY TEXT
    if text.strip() == "":
        return render_template("index.html",
                               prediction="File has no readable text")

    # MODEL PREDICTION
    vector = vectorizer.transform([text])
    prediction = model.predict(vector)[0]
    probability = model.predict_proba(vector)[0]

    phishing_prob = probability[1] * 100
    safe_prob = probability[0] * 100

    result = "🚨 Phishing Email" if prediction == 1 else "✅ Safe Email"

    history.append({
        "text": "Uploaded File",
        "result": result,
        "risk": round(phishing_prob, 2),
        "time": datetime.now().strftime("%H:%M:%S")
    })

    return render_template(
        "index.html",
        prediction=result,
        risk=round(phishing_prob, 2),
        safe=round(safe_prob, 2)
    )


# --------------------------------
# DASHBOARD
# --------------------------------
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html", history=history)


# --------------------------------
# LOGOUT
# --------------------------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# --------------------------------
# RUN APP
# --------------------------------
if __name__ == "__main__":
    app.run(debug=True)