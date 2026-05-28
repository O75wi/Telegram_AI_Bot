 import os
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import uvicorn

# ─────────────────────────────────────────────
#  App Setup
# ─────────────────────────────────────────────
app = FastAPI(title="TelegramMiniApp AI Chat", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
#  Environment Variables
# ─────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
AI_PROVIDER    = os.environ.get("AI_PROVIDER", "gemini")  # "gemini" or "openai"
PORT           = int(os.environ.get("PORT", 8000))

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# ─────────────────────────────────────────────
#  System Prompt
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert AI assistant specialized in two main areas:

1. HTML Code Generation: You create clean, modern, responsive, and beautiful HTML/CSS/JS code. 
   When asked to generate HTML, always provide complete, ready-to-use code with embedded CSS and JS.
   Focus on:
   - Modern design with CSS variables and flexbox/grid
   - Mobile-first responsive design
   - Smooth animations and transitions
   - Dark/light theme support
   - Accessibility best practices

2. Logo Design: You create SVG-based logos and provide detailed design guidance.
   When designing logos, you:
   - Generate complete SVG code that can be used directly
   - Explain the design choices (colors, fonts, shapes, symbolism)
   - Offer multiple variations or color schemes
   - Ensure scalability and versatility

General behavior:
- Always respond in the same language the user writes in (Arabic or English)
- Format code in proper markdown code blocks
- Be concise but thorough
- When generating HTML, always wrap it in
- When generating SVG logos, always wrap them in 
svg code blocks
- Provide brief explanations alongside code
- Ask clarifying questions when requirements are ambiguous"""

# ─────────────────────────────────────────────
#  Data Models
# ─────────────────────────────────────────────
class Message(BaseModel):
    role: str   # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []

# ─────────────────────────────────────────────
#  AI Provider Functions
# ─────────────────────────────────────────────
async def call_gemini(user_message: str, history: List[Message]) -> str:
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set in environment variables.")

    contents = []

    # Build conversation history for Gemini format
    for msg in history:
        role = "user" if msg.role == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg.content}]
        })

    # Add the new user message
    contents.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192,
        }
    }

    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload)
[28/05/2026 12:36 م] 𝖣𝖠𝗆𝖡𝗂 𝖺𝗅 𝖥𝗅𝖺𝗆𝖾𝖭𝖼𝗈: if response.status_code != 200:
        error_detail = response.text
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Gemini API error: {error_detail}"
        )

    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse Gemini response: {str(e)}")


async def call_openai(user_message: str, history: List[Message]) -> str:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set in environment variables.")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Build conversation history for OpenAI format
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    # Add the new user message
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 8192,
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(OPENAI_API_URL, json=payload, headers=headers)

    if response.status_code != 200:
        error_detail = response.text
        raise HTTPException(
            status_code=response.status_code,
            detail=f"OpenAI API error: {error_detail}"
        )

    data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse OpenAI response: {str(e)}")


# ─────────────────────────────────────────────
#  API Routes
# ─────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main HTML page"""
    html_path = os.path.join(os.path.dirname(file), "index.html")
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="index.html not found")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint — receives user message + history, returns AI response"""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Limit history to last 20 messages to avoid token overflow
    limited_history = request.history[-20:] if request.history else []

    if AI_PROVIDER.lower() == "openai":
        reply = await call_openai(request.message, limited_history)
    else:
        reply = await call_gemini(request.message, limited_history)

    return JSONResponse(content={"reply": reply, "provider": AI_PROVIDER})


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return JSONResponse(content={
        "status": "healthy",
        "provider": AI_PROVIDER,
        "gemini_key_set": bool(GEMINI_API_KEY),
        "openai_key_set": bool(OPENAI_API_KEY),
    })


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────
if name == "main":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
        log_level="info"
    )
