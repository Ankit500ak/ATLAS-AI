import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from app.config import settings

logger = logging.getLogger(__name__)


class GoogleService:
    """
    Google Workspace integration for Gmail, Calendar, Drive, and Sheets.
    Provides OAuth2 authentication and API access for connected users.
    """

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/spreadsheets.readonly",
    ]

    def __init__(self):
        self._credentials_cache: Dict[int, object] = {}

    def get_auth_url(self, user_id: int) -> str:
        """Generate OAuth2 authorization URL for user."""
        if not settings.google_client_id or not settings.google_client_secret:
            logger.warning("Google OAuth credentials not configured")
            return ""

        try:
            from google_auth_oauthlib.flow import Flow

            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.google_client_id,
                        "client_secret": settings.google_client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                scopes=self.SCOPES,
                redirect_uri="http://localhost:8000/api/v1/auth/google/callback",
            )
            auth_url, _ = flow.authorization_url(
                access_type="offline",
                state=str(user_id),
                prompt="consent",
            )
            return auth_url
        except Exception as e:
            logger.error(f"Failed to generate auth URL: {e}")
            return ""

    async def handle_callback(self, code: str, user_id: int) -> bool:
        """Handle OAuth2 callback and store credentials."""
        if not settings.google_client_id or not settings.google_client_secret:
            logger.warning("Google OAuth credentials not configured")
            return False

        try:
            from google_auth_oauthlib.flow import Flow
            from google.oauth2.credentials import Credentials

            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.google_client_id,
                        "client_secret": settings.google_client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                scopes=self.SCOPES,
                redirect_uri="http://localhost:8000/api/v1/auth/google/callback",
            )
            flow.fetch_token(code=code)
            credentials = flow.credentials

            self._credentials_cache[user_id] = credentials

            from app.database import async_session_factory
            from app.models.user import User
            from sqlalchemy import select

            async with async_session_factory() as db:
                result = await db.execute(select(User).where(User.telegram_id == user_id))
                user = result.scalar_one_or_none()
                if user:
                    user.google_connected = True
                    user.google_access_token = credentials.token
                    user.google_refresh_token = credentials.refresh_token
                    await db.commit()

            logger.info(f"Google account connected for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to handle Google callback: {e}")
            return False

    async def get_gmail_messages(self, user_id: int, query: str = "", limit: int = 10) -> List[Dict]:
        """Fetch Gmail messages matching a query."""
        try:
            import asyncio
            from googleapiclient.discovery import build

            credentials = await self._get_credentials(user_id)
            if not credentials:
                return []

            def _fetch():
                service = build("gmail", "v1", credentials=credentials)
                results = service.users().messages().list(
                    userId="me", q=query, maxResults=limit
                ).execute()

                messages = []
                for msg in results.get("messages", []):
                    message = service.users().messages().get(
                        userId="me", id=msg["id"], format="metadata",
                        metadataHeaders=["From", "Subject", "Date"]
                    ).execute()

                    headers = {h["name"]: h["value"] for h in message.get("payload", {}).get("headers", [])}
                    messages.append({
                        "id": msg["id"],
                        "from": headers.get("From", ""),
                        "subject": headers.get("Subject", ""),
                        "date": headers.get("Date", ""),
                        "snippet": message.get("snippet", ""),
                    })
                return messages

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _fetch)
        except Exception as e:
            logger.error(f"Failed to fetch Gmail messages for user {user_id}: {e}")
            return []

    async def get_calendar_events(self, user_id: int, days_ahead: int = 7) -> List[Dict]:
        """Fetch upcoming calendar events."""
        try:
            import asyncio
            from googleapiclient.discovery import build
            from datetime import timedelta

            credentials = await self._get_credentials(user_id)
            if not credentials:
                return []

            def _fetch():
                service = build("calendar", "v3", credentials=credentials)
                now = datetime.now(timezone.utc)
                time_max = (now + timedelta(days=days_ahead)).isoformat() + "Z"

                events_result = service.events().list(
                    calendarId="primary",
                    timeMin=now.isoformat() + "Z",
                    timeMax=time_max,
                    maxResults=20,
                    singleEvents=True,
                    orderBy="startTime",
                ).execute()

                events = []
                for event in events_result.get("items", []):
                    start = event["start"].get("dateTime", event["start"].get("date"))
                    events.append({
                        "id": event["id"],
                        "summary": event.get("summary", "No title"),
                        "start": start,
                        "description": event.get("description", ""),
                        "location": event.get("location", ""),
                    })
                return events

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _fetch)
        except Exception as e:
            logger.error(f"Failed to fetch calendar events for user {user_id}: {e}")
            return []

    async def get_drive_files(self, user_id: int, query: str = "", limit: int = 10) -> List[Dict]:
        """Fetch Google Drive files."""
        try:
            import asyncio
            from googleapiclient.discovery import build

            credentials = await self._get_credentials(user_id)
            if not credentials:
                return []

            def _fetch():
                service = build("drive", "v3", credentials=credentials)
                q = query if query else "trashed = false"
                results = service.files().list(
                    q=q, pageSize=limit,
                    fields="files(id, name, mimeType, modifiedTime, size)",
                ).execute()

                files = []
                for f in results.get("files", []):
                    files.append({
                        "id": f["id"],
                        "name": f["name"],
                        "mime_type": f["mimeType"],
                        "modified": f.get("modifiedTime", ""),
                        "size": f.get("size", 0),
                    })
                return files

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _fetch)
        except Exception as e:
            logger.error(f"Failed to fetch Drive files for user {user_id}: {e}")
            return []

    async def get_sheets_data(self, user_id: int, spreadsheet_id: str, range_name: str = "Sheet1") -> List[List]:
        """Fetch Google Sheets data."""
        try:
            import asyncio
            from googleapiclient.discovery import build

            credentials = await self._get_credentials(user_id)
            if not credentials:
                return []

            def _fetch():
                service = build("sheets", "v4", credentials=credentials)
                result = service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                ).execute()
                return result.get("values", [])

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _fetch)
        except Exception as e:
            logger.error(f"Failed to fetch Sheets data for user {user_id}: {e}")
            return []

    async def _get_credentials(self, user_id: int):
        """Get cached or refresh credentials for a user."""
        if user_id in self._credentials_cache:
            return self._credentials_cache[user_id]

        try:
            from google.oauth2.credentials import Credentials
            from app.database import async_session_factory
            from app.models.user import User
            from sqlalchemy import select

            async with async_session_factory() as db:
                result = await db.execute(select(User).where(User.telegram_id == user_id))
                user = result.scalar_one_or_none()

            if user and user.google_access_token:
                credentials = Credentials(
                    token=user.google_access_token,
                    refresh_token=user.google_refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=settings.google_client_id,
                    client_secret=settings.google_client_secret,
                )
                self._credentials_cache[user_id] = credentials
                return credentials

            return None
        except Exception as e:
            logger.error(f"Failed to get credentials for user {user_id}: {e}")
            return None

    async def is_connected(self, user_id: int) -> bool:
        """Check if a user has connected their Google account."""
        if user_id in self._credentials_cache:
            return True
        try:
            from app.database import async_session_factory
            from app.models.user import User
            from sqlalchemy import select

            async with async_session_factory() as db:
                result = await db.execute(select(User).where(User.telegram_id == user_id))
                user = result.scalar_one_or_none()
                return bool(user and user.google_access_token)
        except Exception:
            return False

    async def disconnect(self, user_id: int) -> bool:
        """Disconnect Google account for a user."""
        try:
            self._credentials_cache.pop(user_id, None)

            from app.database import async_session_factory
            from app.models.user import User
            from sqlalchemy import select

            async with async_session_factory() as db:
                result = await db.execute(select(User).where(User.telegram_id == user_id))
                user = result.scalar_one_or_none()
                if user:
                    user.google_connected = False
                    user.google_access_token = None
                    user.google_refresh_token = None
                    await db.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to disconnect Google for user {user_id}: {e}")
            return False


google_service = GoogleService()
