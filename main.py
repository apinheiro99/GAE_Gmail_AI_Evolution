from GmailAIManager import GmailAIManager


def main():
    """
    Entry point of the Gmail AI Evolution system.
    Handles setup, authentication, email processing,
    and displays predictions.
    """

    print("\n🚀 Starting Gmail AI Evolution...\n")

    # Initialize system
    ai_manager = GmailAIManager('credentials.json')

    # Authenticate and initialize AI
    if not ai_manager.setup():
        print("❌ System setup failed. Exiting.")
        return

    try:
        # Fetch and process emails
        emails = ai_manager.process_recent_emails(max_emails=20)

        if not emails:
            print("\n📭 No emails processed.\n")
            return

        # Display results
        print("\n===== 📊 EMAIL ANALYSIS REPORT =====\n")

        for email in emails:
            prediction = email.get('ai_prediction', {})
            headers = email.get('headers', {})

            print(f"📨 Subject: {headers.get('subject', '(no subject)')}")
            print(f"👤 From: {headers.get('from', '(unknown)')}")
            print(f"🤖 AI Prediction: {'SPAM' if prediction.get('is_spam') else 'NOT SPAM'}")
            print(f"🎯 Confidence: {prediction.get('spam_confidence', 0):.2%}")
            print(f"⚠️ Risk Level: {prediction.get('risk_level', 'unknown')}")
            print("-" * 50)

    except Exception as e:
        print(f"\n❌ An error occurred while processing emails: {e}")

    print("\n✔️ Finished.\n")


if __name__ == "__main__":
    main()
