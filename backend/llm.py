import os
import json
import datetime
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("API_KEY") 
)

def parse_command(transcript: str, model="gpt-4o"):
    """
    Parse the STT transcript to determine the user's intent.
    Supported Intents: 'schedule_meeting', 'take_minutes', 'general_query'
    Returns a dict with intent and necessary entities.
    """
    now = datetime.datetime.now().astimezone()
    
    prompt = f"""
You are CasperAI, a voice command center for a student club.
Analyze the user's transcript and output the intent and relevant entities in strict JSON format.

Current time: {now.isoformat()}

Possible intents:
1. "schedule_meeting": User wants to add an event to the calendar.
   Required entities: 
   - "summary": (string) title of the event
   - "description": (string) details
   - "start_time": (ISO format string) start time
   - "end_time": (ISO format string) end time (default to 1 hour after start if not specified)
2. "take_minutes": User wants to summarize meeting minutes or go to the minutes page.
3. "general_query": Anything else.
   Required entities:
   - "reply": (string) A conversational text reply to the user.

Transcript: "{transcript}"

Output only JSON.
"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {"intent": "general_query", "reply": "명령을 이해하지 못했습니다."}

def summarize_minutes(transcript: str, model="gpt-4o"):
    """
    Summarize a meeting transcript into official minutes.
    """
    prompt = f"""
Summarize the following meeting transcript into bullet points:
- Key Discussions
- Action Items
- Decisions Made
Transcript: {transcript}
"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt}]
    )
    return response.choices[0].message.content
