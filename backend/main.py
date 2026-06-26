from __future__ import annotations

import asyncio
import json
import math

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import SocketEvent, SubscribePayload, ZoneSummary
from .risk import ROUTES, assess_route
from .weather import get_weather_report


app = FastAPI(title="Alerta Temprana de Deslizamientos")
app.mount("/assets", StaticFiles(directory="frontend"), name="assets")


class ConnectionStore:
    def __init__(self) -> None:
        self.items: list[dict[str, object]] = []

    def upsert(self, websocket: WebSocket, payload: SubscribePayload) -> None:
        self.items = [item for item in self.items if item["websocket"] is not websocket]
        self.items.append({"websocket": websocket, "payload": payload})

    def remove(self, websocket: WebSocket) -> None:
        self.items = [item for item in self.items if item["websocket"] is not websocket]


store = ConnectionStore()


@app.get("/")
async def index() -> FileResponse:
    return FileResponse("frontend/index.html")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "alerta-temprana-deslizamientos"}


@app.get("/api/routes")
async def routes() -> dict[str, object]:
    return {"routes": [route.model_dump() for route in ROUTES]}


@app.get("/api/zones")
async def zones() -> dict[str, object]:
    summaries: list[ZoneSummary] = []

    for route in ROUTES:
        assessment = assess_route(route.id, route.lat, route.lng)
        weather = await get_weather_report(route.lat, route.lng)
        summaries.append(
            ZoneSummary(
                id=route.id,
                name=route.name,
                department=route.department,
                lat=route.lat,
                lng=route.lng,
                assessment=assessment,
                weather=weather,
            )
        )

    return {"zones": [summary.model_dump() for summary in summaries]}


@app.get("/api/assess")
async def api_assess(route_id: str, lat: float, lng: float) -> dict[str, object]:
    return assess_route(route_id, lat, lng).model_dump()


@app.get("/api/weather")
async def api_weather(lat: float, lng: float) -> dict[str, object]:
    weather = await get_weather_report(lat, lng)
    return weather.model_dump()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "ready", "routes": [route.model_dump() for route in ROUTES]})

    try:
        while True:
            payload = json.loads(await websocket.receive_text())

            if payload.get("type") != "subscribe":
                continue

            subscription = SubscribePayload(
                traveler_id=str(payload.get("traveler_id", "")).strip(),
                traveler_name=str(payload.get("traveler_name", "")).strip(),
                route_id=str(payload.get("route_id", ROUTES[0].id)).strip(),
                lat=float(payload.get("lat", ROUTES[0].lat)),
                lng=float(payload.get("lng", ROUTES[0].lng)),
            )
            store.upsert(websocket, subscription)

            assessment = assess_route(subscription.route_id, subscription.lat, subscription.lng)
            event = SocketEvent(**assessment.model_dump(), type="assessment", traveler_id=subscription.traveler_id, traveler_name=subscription.traveler_name)
            await websocket.send_json(event.model_dump())

    except WebSocketDisconnect:
        store.remove(websocket)


async def broadcast() -> None:
    while True:
        await asyncio.sleep(5)
        for item in list(store.items):
            websocket = item["websocket"]
            payload = item["payload"]

            if not isinstance(payload, SubscribePayload):
                continue

            drift_lat = payload.lat + math.sin(asyncio.get_running_loop().time() / 30) * 0.01
            drift_lng = payload.lng + math.cos(asyncio.get_running_loop().time() / 35) * 0.01
            assessment = assess_route(payload.route_id, drift_lat, drift_lng)
            event_type = "critical" if assessment.level == "critical" else "warning" if assessment.level == "high" else "assessment"
            event = SocketEvent(
                **assessment.model_dump(),
                type=event_type,
                traveler_id=payload.traveler_id,
                traveler_name=payload.traveler_name,
            )

            try:
                await websocket.send_json(event.model_dump())
            except Exception:
                store.remove(websocket)


@app.on_event("startup")
async def startup() -> None:
    asyncio.create_task(broadcast())
