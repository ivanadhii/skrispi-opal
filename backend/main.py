import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db
from models import PT100Reading, DHT22Reading, GY906Reading
import mqtt_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: dict):
        data = json.dumps(message)
        for ws in list(self.active):
            try:
                await ws.send_text(data)
            except Exception:
                self.active.remove(ws)


manager = ConnectionManager()


def ws_broadcast_callback(sensor: str, data: dict):
    message = {"sensor": sensor, "data": data}
    asyncio.run_coroutine_threadsafe(manager.broadcast(message), loop)


loop: asyncio.AbstractEventLoop = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global loop
    loop = asyncio.get_event_loop()
    mqtt_client.register_ws_callback(ws_broadcast_callback)
    mqtt_client.start_mqtt_thread()
    yield


app = FastAPI(title="IoT Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── WebSocket ──────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(ws)


# ── PT100 ──────────────────────────────────────────────────────────────────────

@app.get("/api/pt100/latest")
def pt100_latest(limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(PT100Reading)
        .order_by(PT100Reading.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {"temperature": float(r.temperature), "created_at": r.created_at.isoformat()}
        for r in reversed(rows)
    ]


# ── DHT22 ─────────────────────────────────────────────────────────────────────

@app.get("/api/dht22/latest")
def dht22_latest(limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(DHT22Reading)
        .order_by(DHT22Reading.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "temperature": float(r.temperature),
            "humidity": float(r.humidity),
            "created_at": r.created_at.isoformat(),
        }
        for r in reversed(rows)
    ]


# ── GY906 ─────────────────────────────────────────────────────────────────────

@app.get("/api/gy906/latest")
def gy906_latest(limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(GY906Reading)
        .order_by(GY906Reading.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "object_temp": float(r.object_temp),
            "ambient_temp": float(r.ambient_temp),
            "created_at": r.created_at.isoformat(),
        }
        for r in reversed(rows)
    ]


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}
