from datetime import datetime
from AISpamClassifier import AISpamClassifier
from EmailProcessor import EmailProcessor
from GmailAuthenticator import GmailAuthenticator


class GmailAIManager:
    """
    Main orchestrator class for Gmail AI Evolution system.
    Handles authentication, email processing, feature extraction,
    spam classification, and continuous learning.
    """

    def __init__(self, credentials_file: str):
        """
        Initialize the complete AI email system.

        Args:
            credentials_file: Path to Gmail API credentials JSON.
        """
        self.authenticator = GmailAuthenticator(
            credentials_file,
            'token.json'
        )
        self.processor = EmailProcessor()
        self.classifier = AISpamClassifier()
        self.is_authenticated = False

    # ============================================================
    # SETUP
    # ============================================================
    def setup(self) -> bool:
        """Authenticate Gmail API and initialize AI model."""
        print("🔐 Authenticating with Gmail API...")
        self.is_authenticated = self.authenticator.authenticate()

        if not self.is_authenticated:
            print("❌ Authentication failed!")
            return False

        print("✅ Authentication successful!")
        print("🤖 Initializing AI model...")

        self.classifier.initialize_model()
        print("🤖 AI model ready!")

        return True

    # ============================================================
    # PROCESS EMAILS
    # ============================================================
    def process_recent_emails(self, max_emails: int = 50) -> list:
        """
        Process recent emails and get AI predictions.

        Args:
            max_emails: Maximum number of emails to fetch.

        Returns:
            List of processed emails with AI predictions.
        """
        if not self.is_authenticated:
            raise RuntimeError("System not authenticated. Call setup() first.")

        service = self.authenticator.get_service()

        try:
            results = service.users().messages().list(
                userId='me',
                maxResults=max_emails
            ).execute()
        except Exception as e:
            raise RuntimeError(f"Error fetching messages: {e}")

        messages = results.get('messages', [])
        processed_emails = []

        print(f"📧 Processing {len(messages)} emails...")

        for i, message in enumerate(messages):
            print(f"→ Processing email {i + 1}/{len(messages)}")

            try:
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
            except Exception as e:
                print(f"❌ Error fetching email {message['id']}: {e}")
                continue

            email_data = self._extract_email_data(msg)

            if not email_data or 'features' not in email_data:
                print("⚠️ Skipping email due to invalid data.")
                continue

            prediction = self.classifier.predict(email_data['features'])
            email_data['ai_prediction'] = prediction
            processed_emails.append(email_data)

        return processed_emails

    # ============================================================
    # PARSE EMAIL DATA
    # ============================================================
    def _extract_email_data(self, message: dict) -> dict:
        """
        Extract header, body, and features from raw Gmail message.
        Returns safer and structured email data.
        """
        try:
            payload = message.get('payload', {})
            headers = payload.get('headers', [])
            parts = payload.get('parts', [])

            parsed_headers = self.processor.parse_email_headers(headers)
            body = self.processor.extract_email_body(parts)

            features = self.processor.extract_features({
                'subject': parsed_headers.get('subject', ''),
                'body': body,
                'from': parsed_headers.get('from', '')
            })

            return {
                'id': message.get('id'),
                'headers': parsed_headers,
                'body_preview': (
                    body[:200] + '...' if len(body) > 200 else body
                ),
                'features': features,
                'processed_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ Error extracting email data: {e}")
            return {
                "error": True,
                "message": str(e)
            }

    # ============================================================
    # TRAIN WITH USER FEEDBACK
    # ============================================================
    def train_with_feedback(self, email_id: str, is_spam: bool):
        """
        Use user feedback to improve AI model.

        Args:
            email_id: The Gmail ID of the email being evaluated.
            is_spam: True if user confirms SPAM, False otherwise.
        """
        if not self.is_authenticated:
            raise RuntimeError("System not authenticated.")

        service = self.authenticator.get_service()

        try:
            msg = service.users().messages().get(
                userId='me',
                id=email_id
            ).execute()
        except Exception as e:
            print(f"❌ Error fetching email for feedback: {e}")
            return

        email_data = self._extract_email_data(msg)

        if not email_data or 'features' not in email_data:
            print("⚠️ Cannot train: invalid email data.")
            return

        label = 1 if is_spam else 0

        self.classifier.training_data.append(email_data['features'])
        self.classifier.training_labels.append(label)

        # Retrain every 10 feedback entries
        if len(self.classifier.training_data) % 10 == 0:
            print("🔄 Retraining AI model with new feedback...")
            self.classifier.train(
                self.classifier.training_data,
                self.classifier.training_labels
            )
            print("✅ Model retrained!")
