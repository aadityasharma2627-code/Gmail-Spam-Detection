from googleapiclient.discovery import build
from gmail.gmail_auth import authenticate
import base64


def get_latest_emails(max_results=10):

    creds = authenticate()

    service = build(
        "gmail",
        "v1",
        credentials=creds
    )

    results = service.users().messages().list(
        userId="me",
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])

    emails = []

    for message in messages:

        msg = service.users().messages().get(
            userId="me",
            id=message["id"],
            format="full"
        ).execute()

        subject = ""

        body = ""

        headers = msg["payload"].get("headers", [])

        for header in headers:

            if header["name"] == "Subject":
                subject = header["value"]

        payload = msg["payload"]

        if "parts" in payload:

            for part in payload["parts"]:

                if part["mimeType"] == "text/plain":

                    data = part["body"].get("data")

                    if data:
                        body = base64.urlsafe_b64decode(
                            data
                        ).decode("utf-8", errors="ignore")

        else:

            data = payload["body"].get("data")

            if data:
                body = base64.urlsafe_b64decode(
                    data
                ).decode("utf-8", errors="ignore")

        emails.append({
            "subject": subject,
            "body": body
        })

    return emails