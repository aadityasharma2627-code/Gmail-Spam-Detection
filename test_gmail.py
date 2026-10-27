from gmail.fetch_emails import get_latest_emails

emails = get_latest_emails(5)

for i, email in enumerate(emails, start=1):

    print("=" * 80)

    print(f"Email {i}")

    print("\nSubject:")
    print(email["subject"])

    print("\nBody:")
    print(email["body"][:500])

    print("\n")