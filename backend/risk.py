from __future__ import annotations
from datetime import datetime, timezone
from .models import Assessment, AssessmentFactors, Route

ROUTES = [
    Route(id="bogota-villavicencio", name="Bogotá - Villavicencio", department="Cundinamarca / Meta", lat=4.605, lng=-73.98),
    Route(id="manizales-pereira", name="Manizales - Pereira", department="Caldas / Risaralda", lat=5.072, lng=-75.513),
    Route(id="medellin-quibdo", name="Medellín - Quibdó", department="Antioquia / Chocó", lat=6.253, lng=-75.563),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def route_for(route_id: str) -> Route:
    return next((route for route in ROUTES if route.id == route_id), ROUTES[0])


def level_from_score(score: int) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 35:
        return "moderate"
    return "low"


def recommendation_for(level: str) -> str:
    return {
        "critical": "Evacuar el tramo y activar cierre preventivo inmediato.",
        "high": "Reducir velocidad y enviar una patrulla de verificación.",
        "moderate": "Mantener vigilancia y actualizar el estado periódicamente.",
        "low": "Condiciones estables. Continuar con monitoreo normal.",
    }[level]


def assess_route(route_id: str, lat: float, lng: float) -> Assessment:
    route = route_for(route_id)
    seed = sum(ord(char) for char in f"{route_id}:{lat:.4f}:{lng:.4f}")
    slope = min(100, round(abs(lat) * 1.8 + (seed % 24)))
    moisture = min(100, round(abs(lng % 1) * 100 + ((seed // 3) % 18)))
    vegetation_loss = min(100, round(((seed // 5) % 40) + abs(lat + lng) % 0.5 * 70))
    historical_pressure = min(100, round((slope * 0.32) + (moisture * 0.33) + (vegetation_loss * 0.18) + ((seed % 11) * 2)))
    risk_score = min(100, round((slope * 0.35) + (moisture * 0.3) + (vegetation_loss * 0.2) + (historical_pressure * 0.15)))
    level = level_from_score(risk_score)

    return Assessment(
        route_id=route.id,
        route_name=route.name,
        department=route.department,
        coordinates={"lat": lat, "lng": lng},
        risk_score=risk_score,
        level=level,
        factors=AssessmentFactors(
            slope=slope,
            moisture=moisture,
            vegetation_loss=vegetation_loss,
            historical_pressure=historical_pressure,
        ),
        recommendation=recommendation_for(level),
        generated_at=now_iso(),
    )
