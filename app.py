from flask import Flask, render_template, request, redirect, url_for, session
import pickle
from datetime import datetime
from PyPDF2 import PdfReader

# --------------------------------
# APP CONFIG
# --------------------------------
app = Flask(__name__)
app.secret_key = "supersecretkey"

# --------------------------------
# LOAD MODEL
# --------------------------------
model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# store session history
history = []

# --------------------------------
# LOGIN
# --------------------------------
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "1234":
            session["user"] = username
            return redirect(url_for("home"))
        else:
            return render_template("login.html",
                                   error="Invalid Username or Password")

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
# AI PREDICTION FUNCTION
# --------------------------------
def detect_phishing(text):

    if not text or text.strip() == "":
        return "⚠️ No Content Found", 0, 0

    vector = vectorizer.transform([text])
    prediction = model.predict(vector)[0]
    probability = model.predict_proba(vector)[0]

    safe_prob = probability[0] * 100
    phishing_prob = probability[1] * 100

    # smarter decision logic
    if phishing_prob > 70:
        result = "🚨 Phishing Email"
    elif phishing_prob < 40:
        result = "✅ Safe Email"
    else:
        result = "⚠️ Suspicious Email"

    return result, round(phishing_prob, 2), round(safe_prob, 2)


# --------------------------------
# TEXT CHECK
# --------------------------------
@app.route("/predict", methods=["POST"])
def predict():

    if "user" not in session:
        return redirect(url_for("login"))

    email_text = request.form.get("email", "")

    result, phishing, safe = detect_phishing(email_text)

    history.append({
        "text": email_text[:60],
        "result": result,
        "risk": phishing,
        "time": datetime.now().strftime("%H:%M:%S")
    })

    return render_template(
        "index.html",
        prediction=result,
        risk=phishing,
        safe=safe
    )


# --------------------------------
# FILE UPLOAD CHECK
# --------------------------------
@app.route("/upload", methods=["POST"])
def upload():

    if "user" not in session:
        return redirect(url_for("login"))

    file = request.files.get("file")

    if not file or file.filename == "":
        return render_template("index.html",
                               prediction="⚠️ No file selected")

    text = ""

    # TXT FILE
    if file.filename.endswith(".txt"):
        text = file.read().decode("utf-8", errors="ignore")

    # PDF FILE
    elif file.filename.endswith(".pdf"):
        reader = PdfReader(file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + " "

    else:
        return render_template("index.html",
                               prediction="❌ Unsupported File")

    result, phishing, safe = detect_phishing(text)

    history.append({
        "text": "Uploaded File",
        "result": result,
        "risk": phishing,
        "time": datetime.now().strftime("%H:%M:%S")
    })

    return render_template(
        "index.html",
        prediction=result,
        risk=phishing,
        safe=safe
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
# RUN SERVER
# --------------------------------
if __name__ == "__main__":
    app.run(debug=True)