import os
import re
import json
import threading
import asyncio
from datetime import datetime, date
from decimal import Decimal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from langchain_groq import ChatGroq
from email_service import send_email

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "django_backend", "db.sqlite3")
DB_URI = f"sqlite:///{DB_PATH}"

sql_engine = create_engine(DB_URI, connect_args={"check_same_thread": False})

PLANORAMA_TABLES = ["events_event", "events_guest", "events_rsvp", "messaging_messagelog"]
BLOCKED_KEYWORDS = ["DROP", "DELETE", "ALTER", "TRUNCATE", "CREATE", "ATTACH", "DETACH"]

llm = ChatGroq(
    temperature=0,
    model_name="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY")
)

app = FastAPI(title="Planorama LLM Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"

sessions: dict = {}
_schema_cache = None

SYSTEM_CONTEXT = """
You are Planorama, a friendly and expert AI assistant for wedding event planners.

The database has these tables:
- events_event: wedding events (id, name, date, description)
- events_guest: all registered guests (id, name, email, phone, created_at)
- events_rsvp: RSVP records linking guests to events (id, guest_id, event_id, status, plus_ones)
  - status can only be: 'pending', 'attending', or 'declined'
- messaging_messagelog: email log (id, guest_id, event_id, provider_message_id, status, subject, body, created_at, updated_at)
  - provider_message_id has a UNIQUE constraint. Every row MUST have a different value.
  - created_at and updated_at are NOT NULL. Always use CURRENT_TIMESTAMP for both.

Relationships:
- events_rsvp.guest_id → events_guest.id
- events_rsvp.event_id → events_event.id
- messaging_messagelog.guest_id → events_guest.id
- messaging_messagelog.event_id → events_event.id
"""


def get_schema() -> str:
    try:
        inspector = inspect(sql_engine)
        schema_lines = []
        for table in PLANORAMA_TABLES:
            columns = inspector.get_columns(table)
            col_defs = ", ".join([f"{c['name']} ({str(c['type'])})" for c in columns])
            schema_lines.append(f"Table: {table}\n  Columns: {col_defs}")
        return "\n\n".join(schema_lines)
    except Exception as e:
        return f"Schema unavailable: {e}"


def get_schema_cached() -> str:
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = get_schema()
    return _schema_cache


def clean_sql(raw: str) -> str:
    cleaned = raw.strip()
    cleaned = re.sub(r"```sql", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned)
    return cleaned.strip()


def is_safe_sql(query: str) -> bool:
    query_upper = query.upper()
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", query_upper):
            return False
    return True


def make_json_safe(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


def format_history_for_prompt(history: list) -> str:
    recent = history[-4:]
    lines = []
    for msg in recent:
        role = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def generate_sql_from_question(question: str, history_text: str) -> tuple[str, str]:
    schema = get_schema_cached()

    prompt = f"""{SYSTEM_CONTEXT}

Database Schema:
{schema}

Recent conversation:
{history_text}

User's question: "{question}"

Your task:
1. Write a single SQLite-compatible SQL query to answer the question.
2. For questions about "all people", "all guests", "everyone" → SELECT from events_guest.
3. For listing who is attending/pending/declined → JOIN events_rsvp with events_guest and events_event.
4. NEVER use DROP, DELETE, ALTER, TRUNCATE.
5. Return ONLY the raw SQL. No markdown, no explanation.

CRITICAL RULES FOR WRITE OPERATIONS:

If a user mentions a guest by a partial name and you suspect multiple matches, generate a SELECT query first.
FORBIDDEN: Do NOT generate an UPDATE, DELETE, or INSERT query for an ambiguous name without first verifying it's a unique match.

UPDATE RSVP status:
  UPDATE events_rsvp SET status = '<new_status>'
  WHERE guest_id = (SELECT id FROM events_guest WHERE name = '<FULL_UNIQUE_NAME>');

If the name is not unique or only a first name is provided:
  SELECT id, name, email FROM events_guest WHERE name LIKE '%<partial_name>%';

INSERT emails to ALL guests (no event filter):
  INSERT INTO messaging_messagelog (guest_id, event_id, provider_message_id, status, subject, body, created_at, updated_at)
  SELECT g.id, NULL, hex(randomblob(16)), 'sent', '<subject>', 'Hi ' || g.name || ', <body>', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
  FROM events_guest g;

INSERT emails to guests of a specific event:
  INSERT INTO messaging_messagelog (guest_id, event_id, provider_message_id, status, subject, body, created_at, updated_at)
  SELECT g.id, r.event_id, hex(randomblob(16)), 'sent', '<subject>', 'Hi ' || g.name || ', <body>', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
  FROM events_guest g
  JOIN events_rsvp r ON r.guest_id = g.id
  JOIN events_event e ON e.id = r.event_id
  WHERE e.name LIKE '%<event_name>%';

NEVER use a static string like 'provider_xyz' for provider_message_id. ALWAYS use hex(randomblob(16)).

If the user says "Update Yash's RSVP", do NOT immediately run an UPDATE if there could be multiple. Run a SELECT to check first:
  SELECT id, name, email FROM events_guest WHERE name LIKE '%<guest_name>%';
Only proceed with the UPDATE if you are certain of the identity.
"""

    response = llm.invoke(prompt)
    raw_sql = clean_sql(response.content)

    upper = raw_sql.upper().strip()
    intent = "write" if any(upper.startswith(w) for w in ["INSERT", "UPDATE", "REPLACE"]) else "read"

    return raw_sql, intent


def stream_natural_answer(question: str, sql: str, data: list, intent: str, history_text: str, rows_affected: int = 0):
    data_preview = data[:30]
    data_str = json.dumps(data_preview, default=str, indent=2)

    if intent == "write":
        result_context = f"The database operation completed successfully. {rows_affected} rows were affected."
    else:
        result_context = f"The database returned {len(data)} records:\n{data_str}"

    prompt = f"""{SYSTEM_CONTEXT}

Recent conversation:
{history_text}

The user asked: "{question}"

The SQL query executed was:
{sql}

Result from the database:
{result_context}

Write a clear, concise, friendly response to the user based ONLY on this data.
- Do NOT make up any information not in the results.
- If the results contain multiple guests when the user only asked about one, list the options and ask which one they meant.
- If the result is a list of people, present each name clearly.
- If the result is a count or summary, state it directly.
- Keep it conversational, like a helpful assistant.
- Do not repeat the SQL query or technical details.
"""

    for chunk in llm.stream(prompt):
        if chunk.content:
            yield chunk.content


def _trigger_actual_emails(conn, rows_affected: int):
    try:
        recent_logs = conn.execute(text(
            """SELECT ml.id, ml.guest_id, ml.event_id, ml.subject,
                      g.name as guest_name, g.email as guest_email,
                      e.name as event_name, e.date as event_date
               FROM messaging_messagelog ml
               JOIN events_guest g ON g.id = ml.guest_id
               LEFT JOIN events_event e ON e.id = ml.event_id
               ORDER BY ml.id DESC
               LIMIT :limit"""
        ), {"limit": rows_affected})

        rows = recent_logs.fetchall()
        columns = recent_logs.keys()
        sent = 0
        failed = 0

        for row in rows:
            row_dict = dict(zip(columns, row))
            guest_name = row_dict.get("guest_name", "Guest")
            guest_email = row_dict.get("guest_email", "")
            event_name = row_dict.get("event_name", "Your Event")
            event_date = str(row_dict.get("event_date", "")) if row_dict.get("event_date") else ""
            subject = row_dict.get("subject", f"Regarding {event_name}")

            result = send_email(
                to=guest_email,
                subject=subject,
                guest_name=guest_name,
                event_name=event_name,
                event_date=event_date
            )

            if result["success"]:
                sent += 1
                conn.execute(text(
                    "UPDATE messaging_messagelog SET provider_message_id = :pid WHERE id = :mid"
                ), {"pid": result["id"], "mid": row_dict["id"]})
            else:
                failed += 1
                print(f"[EMAIL] Failed for {guest_name}: {result['error']}")

        conn.commit()
        print(f"[EMAIL] Batch complete: {sent} sent, {failed} failed")

    except Exception as e:
        print(f"[EMAIL] Error in _trigger_actual_emails: {str(e)}")


def process_and_stream(session_id: str, user_message: str):
    if session_id not in sessions:
        sessions[session_id] = []

    history = sessions[session_id]
    history_text = format_history_for_prompt(history)

    try:
        sql_query, intent = generate_sql_from_question(user_message, history_text)

        if not is_safe_sql(sql_query):
            error_msg = "I'm sorry, I cannot perform that operation as it could damage the database."
            sessions[session_id].append({"role": "user", "content": user_message})
            sessions[session_id].append({"role": "assistant", "content": error_msg})
            yield error_msg
            return

        data_result = []
        rows_affected = 0
        with sql_engine.connect() as conn:
            result = conn.execute(text(sql_query))

            if intent == "write":
                conn.commit()
                rows_affected = result.rowcount
                if "messaging_messagelog" in sql_query.lower() and sql_query.upper().strip().startswith("INSERT"):
                    _trigger_actual_emails(conn, rows_affected)
            else:
                columns = result.keys()
                raw_rows = result.fetchall()
                for row in raw_rows:
                    safe_row = {k: make_json_safe(v) for k, v in zip(columns, row)}
                    data_result.append(safe_row)

        full_response = ""
        for chunk in stream_natural_answer(user_message, sql_query, data_result, intent, history_text, rows_affected):
            full_response += chunk
            yield chunk

        sessions[session_id].append({"role": "user", "content": user_message})
        sessions[session_id].append({"role": "assistant", "content": full_response})

    except SQLAlchemyError as e:
        error_msg = f"I had trouble reading the database. Details: {str(e)}"
        yield error_msg
    except Exception as e:
        error_msg = f"Something went wrong: {str(e)}"
        print(f"[ERROR] {error_msg}")
        yield error_msg


@app.get("/health")
def health_check():
    return {"status": "ok", "app": "Planorama LLM Service", "db": DB_PATH}


@app.post("/chat/stream")
async def chat_stream_endpoint(req: ChatRequest):
    if not req.message.strip():
        return {"error": "Message cannot be empty"}

    async def generate():
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()

        def run_sync():
            try:
                for chunk in process_and_stream(req.session_id, req.message):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, f"Error: {str(e)}")
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        thread = threading.Thread(target=run_sync, daemon=True)
        thread.start()

        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    if not req.message.strip():
        return {"error": "Message cannot be empty"}

    full_response = ""
    for chunk in process_and_stream(req.session_id, req.message):
        full_response += chunk

    return {"response": full_response}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
