import datetime
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
BACKEND_DIR = Path(__file__).resolve().parent
CREDENTIALS_PATH = BACKEND_DIR / 'credentials.json'
TOKEN_PATH = BACKEND_DIR / 'token.json'
AUTH_STATE_PATH = BACKEND_DIR / 'calendar_auth_state.json'


def get_calendar_auth_status():
    if not CREDENTIALS_PATH.exists():
        return {
            'configured': False,
            'connected': False,
            'message': 'credentials.json is missing in backend directory.',
        }

    if not TOKEN_PATH.exists():
        return {
            'configured': True,
            'connected': False,
            'message': 'Google Calendar is not connected yet.',
        }

    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        if creds and creds.valid:
            return {
                'configured': True,
                'connected': True,
                'message': 'Google Calendar is connected.',
            }

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with TOKEN_PATH.open('w', encoding='utf-8') as token:
                token.write(creds.to_json())
            return {
                'configured': True,
                'connected': True,
                'message': 'Google Calendar is connected.',
            }
    except Exception as exc:
        return {
            'configured': True,
            'connected': False,
            'message': f'Existing token is invalid: {exc}',
        }

    return {
        'configured': True,
        'connected': False,
        'message': 'Google Calendar is not connected yet.',
    }


def begin_google_calendar_connect():
    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError('credentials.json is missing in backend directory.')

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_PATH),
        SCOPES,
        redirect_uri='http://localhost',
    )
    auth_url, state = flow.authorization_url(access_type='offline', prompt='consent')

    AUTH_STATE_PATH.write_text(
        json.dumps(
            {
                'state': state,
                'redirect_uri': 'http://localhost',
                'code_verifier': getattr(flow, 'code_verifier', None),
            }
        ),
        encoding='utf-8',
    )
    return auth_url


def complete_google_calendar_connect(redirect_response: str):
    if not AUTH_STATE_PATH.exists():
        raise FileNotFoundError('No pending Google Calendar auth session found.')

    auth_state = json.loads(AUTH_STATE_PATH.read_text(encoding='utf-8'))
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_PATH),
        SCOPES,
        state=auth_state.get('state'),
        redirect_uri=auth_state.get('redirect_uri', 'http://localhost'),
    )

    code_verifier = auth_state.get('code_verifier')
    if code_verifier:
        flow.code_verifier = code_verifier

    flow.fetch_token(authorization_response=redirect_response)

    with TOKEN_PATH.open('w', encoding='utf-8') as token:
        token.write(flow.credentials.to_json())

    AUTH_STATE_PATH.unlink(missing_ok=True)
    return True

def authenticate_google_calendar():
    """Authenticate and return the Calendar API service."""
    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError('credentials.json is missing in backend directory.')

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with TOKEN_PATH.open('w', encoding='utf-8') as token:
                token.write(creds.to_json())
        else:
            raise RuntimeError('Google Calendar is not connected. Complete the connect flow from the calendar page first.')
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

def get_upcoming_events(max_results=10, time_min=None, time_max=None):
    """Fetch the upcoming events."""
    service = authenticate_google_calendar()
    request_args = {
        'calendarId': 'primary',
        'timeMin': time_min or (datetime.datetime.utcnow().isoformat() + 'Z'),
        'maxResults': max_results,
        'singleEvents': True,
        'orderBy': 'startTime',
    }
    if time_max:
        request_args['timeMax'] = time_max

    events_result = service.events().list(**request_args).execute()
    events = events_result.get('items', [])
    return events
