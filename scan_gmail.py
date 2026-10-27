from gmail.fetch_emails import get_latest_emails
from predict import predict_email

emails = get_latest_emails(10)

print("=" * 100)
print("SCANNING GMAIL")
print("=" * 100)

for i, email in enumerate(emails, start=1):

    subject = email["subject"]
    body = email["body"]

    prediction, confidence = predict_email(subject, body)

    print("\n" + "=" * 100)

    print(f"Email {i}")

    print("-" * 100)

    print("Subject:")
    print(subject)

    print("\nPrediction:")

    if prediction == 1:
        print("SPAM")
    else:
        print("HAM")

    if confidence is not None:
        print(f"Confidence: {confidence:.2f}%")

    print("\nBody Preview:")
    print(body[:300])

print("\n")
print("=" * 100)
print("Finished")
print("=" * 100)