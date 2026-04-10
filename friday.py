import os
import uuid
from collections import defaultdict
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field

# --- CONFIGURATION ---
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4") # Standardized to gpt-4
BOSS_NAME = os.getenv("BOSS_NAME", "Boss")
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))

SYSTEM_PROMPT = f"""
You are Friday, my personal AI assistant.

Relationship and tone:
- Treat the user as your boss and primary decision-maker.
- Address the user respectfully as {BOSS_NAME}.
- Speak naturally with a confident female Irish accent style in wording.
- Give direct recommendations and short actionable next steps.
""".strip()

# --- MODELS ---
class AskRequest(BaseModel):
    text: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class AskResponse(BaseModel):
    answer: str
    response_id: str | None = None
    session_id: str

# --- APP SETUP ---
app = FastAPI(title="Friday Voice Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure the 'static' folder exists in your repo!
app.mount("/static", StaticFiles(directory="static"), name="static")

SESSION_HISTORY: dict[str, list[dict[str, str]]] = defaultdict(list)

def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)

def _build_input(session_id: str, user_text: str) -> list[dict[str, str]]:
    history = SESSION_HISTORY.get(session_id, [])
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-MAX_HISTORY_MESSAGES:])
    messages.append({"role": "user", "content": user_text})
    return messages

def _remember(session_id: str, user_text: str, assistant_text: str) -> None:
    SESSION_HISTORY[session_id].append({"role": "user", "content": user_text})
    SESSION_HISTORY[session_id].append({"role": "assistant", "content": assistant_text})
    # Keep history within limits
    if len(SESSION_HISTORY[session_id]) > MAX_HISTORY_MESSAGES:
        SESSION_HISTORY[session_id] = SESSION_HISTORY[session_id][-MAX_HISTORY_MESSAGES:]

# --- ROUTES ---
@app.get("/")
def index() -> FileResponse:
    return FileResponse("static/index.html")

@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    client = _client()

    # Corrected OpenAI API call
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=_build_input(payload.session_id, payload.text),
    )

    answer = response.choices[0].message.content.strip()
    _remember(payload.session_id, payload.text, answer)
    
    return AskResponse(
        answer=answer, 
        response_id=response.id, 
        session_id=payload.session_id
    )

@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "sessions": len(SESSION_HISTORY)}
