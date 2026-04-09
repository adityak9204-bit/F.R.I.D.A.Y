# friday
# Friday - Live AI Assistant (Voice + Web)

This project provides a practical assistant scaffold with:

- **Live internet access** through the OpenAI Responses API `web_search_preview` tool.
- **Active listening** in-browser via continuous Speech Recognition.
- **Voice answers** via browser speech synthesis, preferring **Irish English (`en-IE`)** voices when available.
- A customizable assistant persona tuned for a boss/assistant relationship.
- **Session memory** so follow-up requests stay in context.

> Note: No app can literally perform “all tasks” with unrestricted permissions. This scaffold supports a broad set of safe software tasks and web-grounded answering.

---

## Step-by-step: how to use it

### 0) Prerequisites

- Python 3.11+
- Node is optional (only used here for JS syntax checks)
- An OpenAI API key
- Chrome or Edge recommended for best Web Speech API support

### 1) Clone and enter the project

```bash
git clone <your-repo-url>
cd friday
```

### 2) Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Set environment variables

```bash
export OPENAI_API_KEY="your_openai_api_key"
export BOSS_NAME="Your Name"            # optional
export OPENAI_MODEL="gpt-4.1"            # optional
export MAX_HISTORY_MESSAGES="12"         # optional
```

### 5) Start the app

```bash
uvicorn app:app --reload --port 8000
```

### 6) Open the UI

Go to: <http://localhost:8000>

### 7) First-time browser permissions

When prompted, allow **microphone access**.

### 8) Ask questions (two modes)

#### A) Typed mode
1. Enter text in the box.
2. Click **Ask**.
3. Friday replies in text and voice.

#### B) Voice mode (active listening)
1. Click **Start Listening**.
2. Speak naturally.
3. After a short pause, Friday sends your speech and replies.
4. Click **Stop Listening** to pause microphone capture.

### 9) Keep or reset memory

- Friday remembers context within the same browser session ID.
- Click **Reset Memory** when changing topics.

### 10) Daily best-practice prompt

Use this as your first message each day:

> "Friday, today my top priorities are X, Y, Z. Keep answers short, include next actions, and flag risks."

---

## How the app works

- Frontend (`static/app.js`):
  - Captures speech continuously.
  - Debounces speech with a silence timer before sending.
  - Pauses recognition while Friday speaks to reduce echo/feedback loops.
  - Sends `session_id` so follow-up questions retain context.
- Backend (`app.py`):
  - Calls the OpenAI Responses API.
  - Enables live web search tool.
  - Maintains in-memory per-session history.
  - Exposes `/reset/{session_id}` for quick memory reset.

---

## API endpoints

- `GET /` → web UI
- `POST /ask` → assistant reply
- `POST /reset/{session_id}` → clear session memory
- `GET /health` → health + session count

Example request:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"text":"Give me today\'s top AI news in 5 bullets","session_id":"demo-session"}'
```

---

## Troubleshooting

### Microphone not working

- Confirm browser mic permission is allowed.
- Prefer Chrome/Edge.
- Ensure your OS input device is correct.

### No voice output

- Check system volume/output device.
- Verify browser speech synthesis is supported.
- Install additional `en-IE` voices for better Irish-accent quality.

### `OPENAI_API_KEY is not set`

- Re-run `export OPENAI_API_KEY="..."` in the same terminal where you run `uvicorn`.

### Context feels wrong or stale

- Click **Reset Memory**.
- Reduce `MAX_HISTORY_MESSAGES`.

---

## Production notes

- Add authentication and rate-limits to `/ask`.
- Persist memory in a database (instead of in-memory).
- Add task tools (calendar/email/files) behind explicit confirmation flows.
- Add observability: request IDs, latency, and error dashboards.