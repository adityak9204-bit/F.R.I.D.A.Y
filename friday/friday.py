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


OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")
BOSS_NAME = os.getenv("BOSS_NAME", "Boss")
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))

SYSTEM_PROMPT = f"""
You are Friday, my personal AI assistant.

Relationship and tone:
- Treat the user as your boss and primary decision-maker.
- Address the user respectfully as {BOSS_NAME} (or their preferred name if they provide one).
- Be loyal, proactive, and organized like an elite executive assistant.

Behavior requirements:
- Speak naturally and warmly with a confident female Irish accent style in wording.
- Use active listening: briefly acknowledge what the boss said before answering.
- Give direct recommendations, then short actionable next steps.
- Be concise by default, expand when requested.
- If web access is available, use it whenever freshness matters.
- Help with any legal/safe task (planning, writing, coding, analysis, research).
""".strip()


class AskRequest(BaseModel):
    text: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class AskResponse(BaseModel):
    answer: str
    response_id: str | None = None
    session_id: str


app = FastAPI(title="Friday Voice Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory conversational memory by session.
SESSION_HISTORY: dict[str, list[dict[str, str]]] = defaultdict(list)


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def _build_input(session_id: str, user_text: str) -> list[dict[str, str]]:
    history = SESSION_HISTORY.get(session_id, [])
    trimmed = history[-MAX_HISTORY_MESSAGES:]
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        *trimmed,
        {"role": "user", "content": user_text},
    ]


def _remember(session_id: str, user_text: str, assistant_text: str) -> None:
    SESSION_HISTORY[session_id].append({"role": "user", "content": user_text})
    SESSION_HISTORY[session_id].append({"role": "assistant", "content": assistant_text})
    SESSION_HISTORY[session_id] = SESSION_HISTORY[session_id][-MAX_HISTORY_MESSAGES:]


@app.get("/")
def index() -> FileResponse:
    return FileResponse("static/index.html")


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    client = _client()

    response = client.responses.create(
        model=OPENAI_MODEL,
        tools=[{"type": "web_search_preview"}],
        input=_build_input(payload.session_id, payload.text),
    )

    answer = response.output_text.strip()
    _remember(payload.session_id, payload.text, answer)
    return AskResponse(answer=answer, response_id=getattr(response, "id", None), session_id=payload.session_id)


@app.post("/reset/{session_id}")
def reset_session(session_id: str) -> dict[str, Any]:
    SESSION_HISTORY.pop(session_id, None)
    return {"ok": True, "session_id": session_id}


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "sessions": len(SESSION_HISTORY)}
