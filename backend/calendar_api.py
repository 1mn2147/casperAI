import datetime
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
BACKEND_DIR = Path(__file__).resolve().parent
CREDENTIALS_PATH = BACKEND_DIR / 'credentials.json'
TOKEN_PATH = BACKEND_DIR / 'token.json'

def authenticate_google_calendar():
    """Authenticate and return the Calendar API service."""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        with TOKEN_PATH.open('w', encoding='utf-8') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def add_event(summary: str, description: str, start_time: str, end_time: str):
    """
    Add an event to the primary calendar.
    start_time and end_time should be ISO format strings (e.g., '2023-10-10T10:00:00+09:00')
    """
    service = authenticate_google_calendar()
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time,
            'timeZone': 'Asia/Seoul',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Asia/Seoul',
        },
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    return event.get('htmlLink')

def get_upcoming_events(max_results=10):
    """Fetch the upcoming events."""
    service = authenticate_google_calendar()
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events_result = service.events().list(
        calendarId='primary', timeMin=now,
        maxResults=max_results, singleEvents=True,
        orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events
