import os
from openai import OpenAI

# Initialize the OpenAI client. 
# This can be pointed to any Copilot-supported provider (OpenAI, Anthropic via adapter, etc.)
# using standard OPENAI_API_KEY environment variable.
client = OpenAI(
    api_key=os.environ.get("API_KEY") # User's API key for a Copilot-supported model (e.g., GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro)
)

def parse_command(transcript: str, model="gpt-4o"):
    """
    Parse the STT transcript to determine the user's intent.
    Supported Intents: 'schedule_meeting', 'take_minutes', 'general_query'
    """
    prompt = f"""
You are CasperAI, a voice command center.
Analyze the user's transcript and output the intent and relevant entities in JSON format.
Transcript: {transcript}
"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content

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
