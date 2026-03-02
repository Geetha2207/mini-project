from flask import Flask, render_template, request, redirect, url_for, session
import pickle
from datetime import datetime
from PyPDF2 import PdfReader

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -----------------------------
# LOAD MODEL
# -----------------------------
model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

history = []

# -----------------------------
# LOGIN
# -----------------------------
@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":
        if request.form["username"]=="admin" and request.form["password"]=="1234":
            session["user"]="admin"
            return redirect(url_for("home"))
        return render_template("login.html",error="Invalid Login")

    return render_template("login.html")


# -----------------------------
# HOME
# -----------------------------
@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")
    return render_template("index.html")


# -----------------------------
# AI ANALYSIS FUNCTION
# -----------------------------
def analyze(text):

    vector = vectorizer.transform([text])
    prediction = model.predict(vector)[0]
    probability = model.predict_proba(vector)[0]

    phishing_prob = round(probability[1]*100,2)
    safe_prob = round(probability[0]*100,2)

    result = "🚨 Phishing Email" if prediction==1 else "✅ Safe Email"

    # explanation logic
    reasons=[]
    keywords=["verify","password","urgent","click","bank","login"]

    for word in keywords:
        if word in text.lower():
            reasons.append(word)

    return result, phishing_prob, safe_prob, reasons


# -----------------------------
# TEXT PREDICTION
# -----------------------------
@app.route("/predict", methods=["POST"])
def predict():

    if "user" not in session:
        return redirect("/")

    email_text = request.form.get("email","")

    result,risk,safe,reasons = analyze(email_text)

    history.append({
        "text": email_text[:40],
        "result": result,
        "risk": risk,
        "time": datetime.now().strftime("%H:%M:%S")
    })

    return render_template(
        "index.html",
        prediction=result,
        risk=risk,
        safe=safe,
        reasons=reasons
    )


# -----------------------------
# FILE UPLOAD
# -----------------------------
@app.route("/upload", methods=["POST"])
def upload():

    if "user" not in session:
        return redirect("/")

    file = request.files["file"]
    text=""

    if file.filename.endswith(".txt"):
        text=file.read().decode("utf-8")

    elif file.filename.endswith(".pdf"):
        reader=PdfReader(file)
        for page in reader.pages:
            t=page.extract_text()
            if t:
                text+=t

    else:
        return render_template("index.html",
                               prediction="Unsupported File")

    result,risk,safe,reasons = analyze(text)

    history.append({
        "text":"Uploaded File",
        "result":result,
        "risk":risk,
        "time":datetime.now().strftime("%H:%M:%S")
    })

    return render_template(
        "index.html",
        prediction=result,
        risk=risk,
        safe=safe,
        reasons=reasons
    )


# -----------------------------
# DASHBOARD
# -----------------------------
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    return render_template("dashboard.html",history=history)


# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.pop("user",None)
    return redirect("/")


if __name__=="__main__":
    app.run(debug=True)