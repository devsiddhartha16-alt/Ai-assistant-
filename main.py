import os
import requests

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

app = FastAPI(title="JARVIS-X")

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"

GROQ_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL", "openai/gpt-oss-20b"
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL", "gemini-2.5-flash"
)


class ChatRequest(BaseModel):
    message: str
    provider: str = "auto"


def ask_groq(message):
    if not GROQ_KEY:
        raise RuntimeError("Groq API key সেট করা নেই")

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are JARVIS-X, a helpful assistant. "
                        "Reply in Bangla when the user writes Bangla."
                    ),
                },
                {"role": "user", "content": message},
            ],
        },
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Groq error: HTTP {response.status_code}"
        )

    return response.json()["choices"][0]["message"]["content"]


def ask_gemini(message):
    if not GEMINI_KEY:
        raise RuntimeError("Gemini API key সেট করা নেই")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{GEMINI_MODEL}:generateContent"
    )

    response = requests.post(
        url,
        params={"key": GEMINI_KEY},
        json={
            "system_instruction": {
                "parts": [{
                    "text": (
                        "You are JARVIS-X, a helpful assistant. "
                        "Reply in Bangla when the user writes Bangla."
                    )
                }]
            },
            "contents": [{
                "parts": [{"text": message}]
            }],
        },
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Gemini error: HTTP {response.status_code}"
        )

    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


@app.get("/api/health")
def health():
    return {"status": "ok", "assistant": "JARVIS-X"}


@app.post("/api/chat")
def chat(body: ChatRequest):
    message = body.message.strip()

    if not message:
        raise HTTPException(400, "প্রশ্ন লিখুন")

    if len(message) > 6000:
        raise HTTPException(413, "প্রশ্নটি ছোট করুন")

    provider = body.provider.lower()

    if provider not in ("auto", "groq", "gemini"):
        raise HTTPException(400, "Provider: auto, groq অথবা gemini দিন")

    errors = []

    providers = (
        ["groq", "gemini"]
        if provider == "auto"
        else [provider]
    )

    for name in providers:
        try:
            answer = (
                ask_groq(message)
                if name == "groq"
                else ask_gemini(message)
            )

            return {
                "reply": answer,
                "provider": name,
            }

        except Exception as exc:
            errors.append(f"{name}: {str(exc)}")

    raise HTTPException(
        status_code=502,
        detail="কোনো AI provider উত্তর দেয়নি। API key, model ও quota পরীক্ষা করুন।"
    )


if STATIC.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC)),
        name="static"
    )


@app.get("/")
def home():
    page = STATIC / "index.html"

    if page.exists():
        return FileResponse(str(page))

    return {"message": "JARVIS-X is running"}
