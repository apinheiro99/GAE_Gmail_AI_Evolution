import base64
import binascii
import re


class EmailProcessor:
    """
    Processes raw email data into structured format.
    Extracts features for AI model training and prediction.
    """

    def __init__(self):
        self.features = []

    # ============================================================
    # PARSE HEADERS
    # ============================================================
    @staticmethod
    def parse_email_headers(headers: list) -> dict:
        """
        Extract and parse email headers into structured data.
        """
        parsed_headers = {}

        for header in headers:
            name = header.get('name', '').lower()
            value = header.get('value', '')
            parsed_headers[name] = value

        return {
            'from': parsed_headers.get('from', ''),
            'to': parsed_headers.get('to', ''),
            'subject': parsed_headers.get('subject', ''),
            'date': parsed_headers.get('date', ''),
            'message_id': parsed_headers.get('message-id', '')
        }

    # ============================================================
    # EXTRACT BODY
    # ============================================================
    @staticmethod
    def extract_email_body(message_parts: list) -> str:
        """
        Extract and decode the email plain-text body content.
        Supports nested MIME parts.
        """
        body_text = ""

        def traverse(parts):
            nonlocal body_text

            for part in parts:
                mime_type = part.get('mimeType', '')
                body_data = part.get('body', {}).get('data', '')

                if mime_type == 'text/plain' and body_data:
                    try:
                        decoded_bytes = base64.urlsafe_b64decode(body_data + "===")
                        body_text += decoded_bytes.decode('utf-8', errors='replace')
                    except (binascii.Error, UnicodeDecodeError):
                        # ignore malformed blocks
                        continue

                # Recursively check nested parts
                if 'parts' in part:
                    traverse(part['parts'])

        traverse(message_parts)
        return body_text.strip()

    # ============================================================
    # FEATURE EXTRACTION
    # ============================================================
    def extract_features(self, email_data: dict) -> dict:
        """
        Extract ML features from structured email data.
        """
        subject = email_data.get('subject', '') or ""
        body = email_data.get('body', '') or ""
        sender = email_data.get('from', '') or ""
        to_field = email_data.get('to', '') or ""

        return {
            'subject': subject,
            'body': body,
            'from': sender,

            # Numerical features
            'subject_length': len(subject),
            'body_length': len(body),
            'number_of_recipients': len(to_field.split(',')) if to_field else 1,

            # Boolean features
            'has_exclamation_subject': '!' in subject,
            'contains_links': 'http' in body.lower(),
            'has_urgency_words': self._check_urgency_words(subject + " " + body),

            # Text analytics
            'sender_domain': self._extract_domain(sender),
            'capital_ratio': self._calculate_capital_ratio(subject),
        }

    # ============================================================
    # UTILITIES
    # ============================================================
    @staticmethod
    def _check_urgency_words(text: str) -> bool:
        """Check for urgency-related words."""
        urgency_words = ['urgent', 'asap', 'important', 'attention', 'immediately']
        text = text.lower()
        return any(word in text for word in urgency_words)

    @staticmethod
    def _extract_domain(email: str) -> str:
        """Extract domain from sender email address."""
        match = re.search(r'@([A-Za-z0-9.-]+)', email)
        return match.group(1).lower() if match else ""

    @staticmethod
    def _calculate_capital_ratio(text: str) -> float:
        """Calculate the ratio of uppercase letters in the subject."""
        if not text:
            return 0.0

        total = len(text)
        capitals = sum(1 for c in text if c.isupper())

        return capitals / total if total > 0 else 0.0
