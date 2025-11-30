import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError

class GmailAuthenticator:
    """
    Handles secure OAuth2 authentication with Gmail API.
    Manages token refresh, validation, and service creation.
    """

    # Gmail scope (read-only).  
    # If you want to send/modify later: change to gmail.modify or gmail.send.
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, credentials_file: str, token_file: str):
        """
        Initialize authenticator with credential file paths.
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None

    # ============================================================
    # AUTHENTICATION
    # ============================================================
    def authenticate(self) -> bool:
        """
        Perform OAuth2 authentication.
        Creates token.json automatically after the first login.
        Returns True if successful.
        """
        try:
            creds = None

            # -----------------------------------------------
            # LOAD TOKEN IF EXISTS
            # -----------------------------------------------
            if os.path.exists(self.token_file):
                try:
                    creds = Credentials.from_authorized_user_file(
                        self.token_file,
                        self.SCOPES
                    )
                except RefreshError:
                    print("⚠️ Token file is invalid or corrupted. Deleting...")
                    os.remove(self.token_file)
                    creds = None

            # -----------------------------------------------
            # NO VALID CREDS → LOGIN FLOW
            # -----------------------------------------------
            if not creds or not creds.valid:
                # Try refresh first
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except RefreshError:
                        print("⚠️ Refresh failed. Starting full login flow...")
                        creds = None

                # Full OAuth flow
                if not creds:
                    if not os.path.exists(self.credentials_file):
                        raise FileNotFoundError(
                            f"Credentials file not found: {self.credentials_file}"
                        )

                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file,
                        self.SCOPES
                    )

                    # If port 0 fails, try fallbacks
                    try:
                        creds = flow.run_local_server(port=0)
                    except RefreshError:
                        creds = flow.run_local_server(port=8080)

                # Save new token
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())

            # -----------------------------------------------
            # BUILD GMAIL SERVICE
            # -----------------------------------------------
            self.service = build('gmail', 'v1', credentials=creds)

            return True

        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False

    # ============================================================
    # RETURN GMAIL API SERVICE
    # ============================================================
    def get_service(self):
        """Return authenticated Gmail API service."""
        if not self.service:
            raise RuntimeError("Gmail service not initialized. Call authenticate().")

        return self.service
