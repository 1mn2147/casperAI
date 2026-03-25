import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from .stt_tts import transcribe_audio, synthesize_speech
from .llm import parse_command, summarize_minutes
from .calendar_api import (
    get_upcoming_events,
    add_event,
    get_calendar_auth_status,
    begin_google_calendar_connect,
    complete_google_calendar_connect,
    list_accessible_calendars,
)
from .database import save_minutes, update_minutes, get_latest_minutes, get_minutes_by_id

BACKEND_DIR = Path(__file__).resolve().parent
SCREENS_DIR = BACKEND_DIR.parent / "frontend" / "src" / "screens"
TMP_DIR = BACKEND_DIR / "tmp"
TMP_DIR.mkdir(exist_ok=True)

app = FastAPI(title="CasperAI Backend")

app.mount("/static", StaticFiles(directory=str(SCREENS_DIR)), name="static")


def infer_minutes_title(transcript: str, fallback: str = "새로운 회의록") -> str:
    for raw_line in transcript.splitlines():
        line = raw_line.strip()
        if line:
            return line[:80]

    compact = " ".join(transcript.split()).strip()
    if compact:
        return compact[:80]

    return fallback

@app.get("/", response_class=HTMLResponse)
def read_root():
    with (SCREENS_DIR / "dashboard_overview.html").open("r", encoding="utf-8") as f:
        return f.read()

@app.get("/calendar", response_class=HTMLResponse)
def get_calendar_view():
    with (SCREENS_DIR / "calendar_management.html").open("r", encoding="utf-8") as f:
        return f.read()

@app.get("/minutes", response_class=HTMLResponse)
def get_minutes_view():
    with (SCREENS_DIR / "meeting_minutes.html").open("r", encoding="utf-8") as f:
        return f.read()

@app.get("/command", response_class=HTMLResponse)
def get_command_view():
    with (SCREENS_DIR / "voice_ai_command_center.html").open("r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/voice-command")
async def handle_voice_command(audio: UploadFile = File(...)):
    safe_filename = Path(audio.filename or "command.webm").name
    temp_path = TMP_DIR / f"temp_{safe_filename}"
    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)
    
    try:
        transcript = transcribe_audio(str(temp_path))
        parsed = parse_command(transcript)
        intent = parsed.get("intent")
        
        reply_text = "명령을 처리했습니다."
        
        if intent == "schedule_meeting":
            try:
                summary = parsed.get("summary", "New Meeting")
                desc = parsed.get("description", "")
                start = parsed.get("start_time")
                end = parsed.get("end_time")
                if isinstance(start, str) and isinstance(end, str):
                    add_event(summary, desc, start, end)
                    reply_text = f"구글 캘린더에 {summary} 일정을 추가했습니다."
                else:
                    reply_text = "일정 시간 정보를 정확히 이해하지 못했습니다. 다시 말씀해 주세요."
            except Exception as e:
                reply_text = f"일정 추가 중 오류가 발생했습니다: {str(e)}"
                
        elif intent == "take_minutes":
            reply_text = "회의록 작성 페이지로 이동하겠습니다."
            
        elif intent == "general_query":
            reply_text = parsed.get("reply", "네, 알겠습니다.")
            
        tts_filename = f"response_{safe_filename}.mp3"
        tts_output_path = TMP_DIR / tts_filename
        synthesize_speech(reply_text, str(tts_output_path))
        
        return {
            "status": "success",
            "transcript": transcript,
            "intent": parsed,
            "reply": reply_text,
            "audio_response_url": f"/api/audio/{tts_filename}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if temp_path.exists():
            temp_path.unlink()

@app.get("/api/audio/{filename}")
def get_audio_response(filename: str):
    return FileResponse(TMP_DIR / Path(filename).name)

@app.get("/api/events")
def fetch_events(
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = Query(100, ge=1, le=250),
    calendar_ids: Optional[List[str]] = Query(default=None),
):
    try:
        events = get_upcoming_events(
            max_results=limit,
            time_min=start,
            time_max=end,
            calendar_ids=calendar_ids,
        )
        return {"status": "success", "events": events}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/calendars")
def fetch_calendars():
    try:
        calendars = list_accessible_calendars()
        return {"status": "success", "calendars": calendars}
    except Exception as e:
        return {"status": "error", "message": str(e)}

class MinutesRequest(BaseModel):
    transcript: str
    title: Optional[str] = None
    id: Optional[int] = None


class CalendarConnectCompleteRequest(BaseModel):
    redirect_response: str


class CalendarEventRequest(BaseModel):
    summary: str
    description: Optional[str] = ""
    start_time: str
    end_time: str


@app.get("/api/calendar/status")
def calendar_status():
    return {"status": "success", **get_calendar_auth_status()}


@app.post("/api/calendar/connect-url")
def calendar_connect_url():
    try:
        auth_url = begin_google_calendar_connect()
        return {"status": "success", "auth_url": auth_url}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/calendar/complete")
def calendar_connect_complete(req: CalendarConnectCompleteRequest):
    try:
        complete_google_calendar_connect(req.redirect_response)
        return {"status": "success", **get_calendar_auth_status()}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/events")
def create_event(req: CalendarEventRequest):
    try:
        start_dt = datetime.fromisoformat(req.start_time)
        end_dt = datetime.fromisoformat(req.end_time)
        if end_dt <= start_dt:
            return {"status": "error", "message": "End time must be after start time."}

        html_link = add_event(req.summary, req.description or "", req.start_time, req.end_time)
        return {"status": "success", "htmlLink": html_link}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/summarize")
def generate_minutes(req: MinutesRequest):
    try:
        summary = summarize_minutes(req.transcript)
        requested_title = (req.title or "").strip()

        if req.id is not None:
            existing_minute = get_minutes_by_id(req.id)
            if not existing_minute:
                return {"status": "error", "message": "Not found"}

            existing_title = (existing_minute.get("title") or "").strip()
            title = requested_title or existing_title
            if not title or title == "새로운 회의록":
                title = infer_minutes_title(req.transcript)
            updated = update_minutes(req.id, title, req.transcript, summary)
            if not updated:
                return {"status": "error", "message": "Not found"}
            min_id = req.id
        else:
            title = requested_title or infer_minutes_title(req.transcript)
            min_id = save_minutes(title, req.transcript, summary)
        return {"status": "success", "summary": summary, "id": min_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/minutes")
def fetch_latest_minutes(limit: int = Query(5, ge=1)):
    try:
        minutes = get_latest_minutes(limit)
        return {"status": "success", "minutes": minutes}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/minutes/{min_id}")
def fetch_minutes_by_id(min_id: int):
    try:
        minute = get_minutes_by_id(min_id)
        if minute:
            return {"status": "success", "minute": minute}
        return {"status": "error", "message": "Not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
