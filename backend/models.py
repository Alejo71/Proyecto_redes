from __future__ import annotations

from pydantic import BaseModel


class Route(BaseModel):
    id: str
    name: str
    department: str
    lat: float
    lng: float


class AssessmentFactors(BaseModel):
    slope: int
    moisture: int
    vegetation_loss: int
    historical_pressure: int


class Assessment(BaseModel):
    route_id: str
    route_name: str
    department: str
    coordinates: dict[str, float]
    risk_score: int
    level: str
    factors: AssessmentFactors
    recommendation: str
    generated_at: str


class WeatherReport(BaseModel):
    temperature: float
    wind_speed: float
    precipitation: float
    weather_code: int
    description: str
    source: str


class ZoneSummary(BaseModel):
    id: str
    name: str
    department: str
    lat: float
    lng: float
    assessment: Assessment
    weather: WeatherReport


class SubscribePayload(BaseModel):
    traveler_id: str
    traveler_name: str
    route_id: str
    lat: float
    lng: float


class SocketEvent(Assessment):
    type: str
    traveler_id: str
    traveler_name: str
