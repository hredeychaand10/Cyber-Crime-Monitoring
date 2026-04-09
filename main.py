from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import asyncio
import json
from datetime import datetime

from analyzer import analyze_message

app = FastAPI(title="CyberWatch")

messages: list[dict] = []
admin_queues: list[asyncio.Queue] = []


class MessageIn(BaseModel):
    sender: str
    content: str


@app.get("/")
def root():
    return FileResponse("static/index.html")


@app.get("/admin")
def admin_page():
    return FileResponse("static/admin.html")


@app.post("/send")
async def send(body: MessageIn):
    analysis = analyze_message(body.content)
    msg = {
        "id": len(messages) + 1,
        "sender": body.sender.strip() or "Anonymous",
        "content": body.content,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "analysis": analysis,
    }
    messages.append(msg)

    if analysis["is_flagged"]:
        for q in admin_queues:
            await q.put(msg)

    return msg


@app.get("/messages")
def get_messages():
    return messages


@app.post("/clear")
async def clear_session():
    messages.clear()
    return {"ok": True}


@app.get("/admin/flagged")
def get_flagged():
    return [m for m in messages if m["analysis"]["is_flagged"]]


@app.get("/admin/stream")
async def admin_stream():
    """Server-Sent Events stream — sends only NEW flagged messages."""
    q: asyncio.Queue = asyncio.Queue()
    admin_queues.append(q)

    async def gen():
        try:
            while True:
                m = await q.get()
                yield f"data: {json.dumps(m)}\n\n"
        finally:
            if q in admin_queues:
                admin_queues.remove(q)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


app.mount("/static", StaticFiles(directory="static"), name="static")
