import os
import shutil
import json
from typing import Optional
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from .stt_tts import transcribe_audio, synthesize_speech
from .llm import parse_command, summarize_minutes
from .calendar_api import get_upcoming_events, add_event
from .database import save_minutes, update_minutes, get_latest_minutes, get_minutes_by_id

app = FastAPI(title="CasperAI Backend")

app.mount("/static", StaticFiles(directory="frontend/src/screens"), name="static")

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("frontend/src/screens/dashboard_overview.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/calendar", response_class=HTMLResponse)
def get_calendar_view():
    with open("frontend/src/screens/calendar_management.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/minutes", response_class=HTMLResponse)
def get_minutes_view():
    with open("frontend/src/screens/meeting_minutes.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/command", response_class=HTMLResponse)
def get_command_view():
    with open("frontend/src/screens/voice_ai_command_center.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/voice-command")
async def handle_voice_command(audio: UploadFile = File(...)):
    temp_path = f"temp_{audio.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)
    
    try:
        transcript = transcribe_audio(temp_path)
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
            
        tts_output = f"response_{audio.filename}.mp3"
        synthesize_speech(reply_text, tts_output)
        
        return {
            "status": "success",
            "transcript": transcript,
            "intent": parsed,
            "reply": reply_text,
            "audio_response_url": f"/api/audio/{tts_output}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/api/audio/{filename}")
def get_audio_response(filename: str):
    return FileResponse(filename)

@app.get("/api/events")
def fetch_events():
    try:
        events = get_upcoming_events()
        return {"status": "success", "events": events}
    except Exception as e:
        return {"status": "error", "message": str(e)}

class MinutesRequest(BaseModel):
    transcript: str
    title: Optional[str] = None
    id: Optional[int] = None

@app.post("/api/summarize")
def generate_minutes(req: MinutesRequest):
    try:
        summary = summarize_minutes(req.transcript)

        if req.id is not None:
            existing_minute = get_minutes_by_id(req.id)
            if not existing_minute:
                return {"status": "error", "message": "Not found"}

            title = req.title or existing_minute.get("title") or "새로운 회의록"
            updated = update_minutes(req.id, title, req.transcript, summary)
            if not updated:
                return {"status": "error", "message": "Not found"}
            min_id = req.id
        else:
            title = req.title or "새로운 회의록"
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
