import os
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from .stt_tts import transcribe_audio, synthesize_speech
from .llm import parse_command, summarize_minutes
from .calendar_api import get_upcoming_events, add_event

app = FastAPI(title="CasperAI Backend")

# 프론트엔드 정적 파일 마운트
app.mount("/static", StaticFiles(directory="frontend/src/screens"), name="static")

@app.get("/", response_class=HTMLResponse)
def read_root():
    """메인 화면(대시보드) 반환"""
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
    """음성 명령 처리 API: STT -> LLM 의도 파악"""
    temp_path = f"temp_{audio.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)
    
    try:
        # 1. 음성을 텍스트로 변환 (STT)
        transcript = transcribe_audio(temp_path)
        
        # 2. 텍스트를 LLM에 넘겨 의도 분석
        intent = parse_command(transcript)
        
        # 3. 임시로 시스템 대답 생성 (TTS)
        reply_text = f"다음과 같이 인식되었습니다: {transcript}"
        tts_output = f"response_{audio.filename}.mp3"
        synthesize_speech(reply_text, tts_output)
        
        return {
            "status": "success",
            "transcript": transcript,
            "intent": intent,
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
    """캘린더 이벤트 가져오기 API"""
    try:
        events = get_upcoming_events()
        return {"status": "success", "events": events}
    except Exception as e:
        return {"status": "error", "message": str(e)}

class MinutesRequest(BaseModel):
    transcript: str

@app.post("/api/summarize")
def generate_minutes(req: MinutesRequest):
    """회의록 요약 API"""
    try:
        summary = summarize_minutes(req.transcript)
        return {"status": "success", "summary": summary}
    except Exception as e:
        return {"status": "error", "message": str(e)}
