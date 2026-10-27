import threading
from datetime import datetime
import secrets

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from gmail.fetch_emails import get_latest_emails
from predict import predict_email
from gemma_helper import explain_email, warmup

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# -------------------------------
# Server-side storage for scanned emails
# -------------------------------
scan_state = {
    "gmail_results": [],
    "spam_count": 0,
    "ham_count": 0,
    "total": 0,
    "last_scan": None,
}


@app.route("/")
def index():
    return render_template(
        "index.html",
        gmail_results=scan_state["gmail_results"],
        spam_count=scan_state["spam_count"],
        ham_count=scan_state["ham_count"],
        total=scan_state["total"],
        last_scan=scan_state["last_scan"],
        prediction_result=session.pop("prediction_result", None),
        confidence_result=session.pop("confidence_result", None),
        subject_input=session.pop("subject_input", ""),
        body_input=session.pop("body_input", ""),
    )


@app.route("/scan", methods=["POST"])
def scan():
    max_results = int(request.form.get("max_results", 10))
    print("Requested:", max_results)

    emails = get_latest_emails(max_results)
    print("Fetched:", len(emails))

    gmail_results = []
    spam_count = 0
    ham_count = 0

    for email in emails:
        prediction, confidence = predict_email(email["subject"], email["body"])
        label = "SPAM" if prediction == 1 else "HAM"
        if label == "SPAM":
            spam_count += 1
        else:
            ham_count += 1

        gmail_results.append({
            "subject": email["subject"],
            "body": email["body"][:350],
            "full_body": email["body"][:2000],  # Gemma ke liye zyada text
            "prediction": label,
            "confidence": round(confidence, 2) if confidence is not None else None,
        })

    scan_state["gmail_results"] = gmail_results
    scan_state["spam_count"] = spam_count
    scan_state["ham_count"] = ham_count
    scan_state["total"] = len(gmail_results)
    scan_state["last_scan"] = datetime.now().strftime("%d %b %Y %I:%M %p")

    return redirect(url_for("index"))


@app.route("/predict", methods=["POST"])
def predict():
    subject = request.form.get("subject", "")
    body = request.form.get("body", "")

    prediction, confidence = predict_email(subject, body)

    session["prediction_result"] = "SPAM" if prediction == 1 else "HAM"
    session["confidence_result"] = round(confidence, 2) if confidence is not None else None
    session["subject_input"] = subject
    session["body_input"] = body

    return redirect(url_for("index"))


@app.route("/explain", methods=["POST"])
def explain():
    """Gemma 4 (Ollama) se email ka reason aur red flags nikalta hai."""
    data = request.get_json(silent=True) or {}

    if "index" in data:
        try:
            item = scan_state["gmail_results"][int(data["index"])]
        except (ValueError, IndexError):
            return jsonify({"error": "Email nahi mila. Dobara Scan Gmail karo."}), 404
        subject = item["subject"]
        body = item.get("full_body", item["body"])
    else:
        subject = data.get("subject", "")
        body = data.get("body", "")

    if not (subject.strip() or body.strip()):
        return jsonify({"error": "Subject ya body khali hai."}), 400

    result = explain_email(subject, body)
    if not result:
        return jsonify({"error": "Gemma available nahi hai. Ollama chal raha hai?"}), 503
    return jsonify(result)


@app.route("/clear", methods=["POST"])
def clear():
    scan_state["gmail_results"] = []
    scan_state["spam_count"] = 0
    scan_state["ham_count"] = 0
    scan_state["total"] = 0
    scan_state["last_scan"] = None

    session.clear()

    return redirect(url_for("index"))


if __name__ == "__main__":
    # App start hote hi Gemma ko background mein RAM mein load kar do
    threading.Thread(target=warmup, daemon=True).start()
    app.run(debug=True)