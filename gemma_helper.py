import json
import re
from urllib.parse import urlparse

import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "gemma4:e2b"

# (connect timeout, wait-for-next-chunk timeout) seconds.
# Streaming use hota hai, isliye model dheema ho tab bhi chalta rahega.
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


def shorten_links(text):
    """Lambe tracking links ko '[link: domain]' bana deta hai.
    Isse prompt chhota hota hai (jawab jaldi aata hai) aur domain bhi dikhta hai."""
    def repl(m):
        try:
            domain = urlparse(m.group(0)).netloc or "unknown"
        except Exception:
            domain = "unknown"
        return f"[link: {domain}]"
    return re.sub(r"https?://\S+", repl, text)


def parse_gemma_output(text):
    """Model ke text se JSON nikalta hai. Adhura JSON ho to bhi koshish karta hai."""
    text = re.sub(r"```(?:json)?", "", text).strip()

    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    # Adhura / kharab JSON: verdict aur reason alag se nikalo
    v = re.search(r'"verdict"\s*:\s*"(spam|promotional|ham)"', text, re.I)
    if v:
        reason = re.search(r'"reason"\s*:\s*"([^"]*)', text)
        flags = re.findall(r'"([^"]{3,60})"', text.split('"red_flags"')[-1]) if '"red_flags"' in text else []
        return {
            "verdict": v.group(1).lower(),
            "reason": reason.group(1).strip() if reason else "",
            "red_flags": flags[:3],
        }
    return None


def explain_email(subject, body):
    clean_body = shorten_links(body)[:500]
    prompt = f"""You are an email security assistant.
Classify the email as exactly one of:
- "spam": scams, phishing, fake prizes, requests for passwords/money/bank details, or clearly deceptive links.
- "promotional": legitimate marketing or newsletters from real companies. Tracking links, "view web version" and unsubscribe text are NORMAL here.
- "ham": normal personal, work or transactional email.
Links are shown as [link: domain]. Links to well-known brands (adobe.com, google.com, amazon.com etc.) are NOT suspicious by themselves.
Only say "spam" if there is clear deception, a scam, or a request for sensitive data.
Reply ONLY with JSON: {{"verdict": "spam" or "promotional" or "ham", "reason": "one short sentence", "red_flags": ["max 3 items, each under 6 words"]}}

Subject: {subject}
Body: {clean_body}
"""
    # Pehli koshish fail ho to ek baar dobara try karo
    for attempt in (1, 2):
        try:
            text = _call(prompt, 220)
            result = parse_gemma_output(text)
            if result:
                return result
            print(f"Gemma output samajh nahi aaya (try {attempt}):", repr(text[:300]))
        except Exception as e:
            print(f"Gemma error (try {attempt}):", e)
    return None