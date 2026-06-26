# Proyecto_redes

Prototipo simple de alerta temprana para deslizamientos de tierra en carreteras de Colombia. La interfaz principal muestra un mapa de Colombia, zonas problemáticas y clima actual por coordenadas.

## Estructura

- `backend/`: API, WebSocket, evaluación de riesgo y clima.
- `frontend/`: HTML, CSS y JavaScript del cliente con mapa.
- `requirements.txt`: dependencias Python.

## Flujo de la aplicación

1. El navegador carga el tablero y pide `/api/zones`.
2. El backend responde con los corredores, su riesgo y el clima actual.
3. El frontend pinta el mapa, los marcadores y la lista de zonas.
4. Al seleccionar una zona, el cliente consulta `/api/assess` y `/api/weather`.
5. Al conectar la alerta, el backend abre `/ws` y empuja eventos en tiempo real.

## Ejecución local

1. Instala dependencias con `pip install -r requirements.txt`.
2. Inicia el backend con `uvicorn backend.main:app --reload`.
3. Abre `http://127.0.0.1:8000`.

## API

- `GET /api/health`: estado del servicio.
- `GET /api/routes`: corredores simulados.
- `GET /api/zones`: zonas con riesgo y clima.
- `GET /api/assess?route_id=...&lat=...&lng=...`: evaluación por coordenadas.
- `GET /api/weather?lat=...&lng=...`: clima actual.
- `WS /ws`: canal en tiempo real para alertas.

