import json
import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "gemma4:e2b"

# (connect timeout, wait-for-next-chunk timeout) seconds.
# Streaming use hota hai, isliye model dheema ho tab bhi chalta rahega.
# Pehli baar model load hone mein 2-3 minute lag sakte hain, isliye 300.
TIMEOUT = (5, 300)


def _call(prompt, num_predict):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": True,
        "think": False,
        "keep_alive": "24h",
        "options": {"num_ctx": 2048, "temperature": 0.2, "num_predict": num_predict},
    }
    text = ""
    with requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT, stream=True) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            text += chunk.get("response", "")
            if chunk.get("done"):
                break
    return text.strip()


def warmup():
    """Model ko pehle se RAM mein load kar deta hai (app start pe ek baar)."""
    try:
        _call("Say hi", 5)
        print("Gemma warmup done")
    except Exception as e:
        print("Gemma warmup failed:", e)


def explain_email(subject, body):
    prompt = f"""You are an email security assistant.
Classify the email as exactly one of:
- "spam": scams, phishing, fake prizes, requests for passwords/money/bank details, or clearly deceptive links.
- "promotional": legitimate marketing or newsletters from real companies. Long tracking links, "view web version" and unsubscribe text are NORMAL here.
- "ham": normal personal, work or transactional email.
Long tracking URLs from well-known brands (adobe.com, google.com, amazon.com etc.) are NOT suspicious by themselves.
Only say "spam" if there is clear deception, a scam, or a request for sensitive data.
Reply ONLY with JSON: {{"verdict": "spam" or "promotional" or "ham", "reason": "one short sentence", "red_flags": ["max 3 items, each under 6 words"]}}

Subject: {subject}
Body: {body[:600]}
"""
    # Pehli koshish fail ho to ek baar dobara try karo
    for attempt in (1, 2):
        try:
            text = _call(prompt, 100)
            start, end = text.find("{"), text.rfind("}")
            return json.loads(text[start:end + 1])
        except Exception as e:
            print(f"Gemma error (try {attempt}):", e)
    return None