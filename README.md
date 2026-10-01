# Futbot – Backend (FastAPI)

API REST + WebSockets del proyecto Futbot.

## Cómo levantarlo

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

- Swagger (probar endpoints): http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Cómo correr los tests

```bash
pytest                 # todos
pytest tests/unit      # solo unitarios
pytest tests/api       # solo endpoints
pytest -v              # más detalle
```

Los tests pendientes aparecen como `skipped`. Al hacer un requerimiento, se le saca el `@pytest.mark.skip`
y se escribe el test.

## Estructura

```
app/
├── main.py            # arma la app: routers, CORS, arranque
├── core/              # config, base de datos, seguridad (JWT), dependencias, manager de WebSockets
├── models/            # TABLAS de la base de datos (SQLAlchemy)
├── schemas/           # FORMATO de los JSON que entran/salen (Pydantic)
├── routers/           # ENDPOINTS: reciben el request y delegan al service
├── services/          # LÓGICA de cada requerimiento (acá se trabaja casi todo)
├── engine/            # motor que juega el partido (REQ 14, 15)
└── behaviors/         # comportamientos por default en Python (REQ 4, 5)
tests/
├── unit/              # tests de services, engine, comportamientos
└── api/               # tests de endpoints
```

Flujo de un request: `router` → `service` → `model` (DB), y la respuesta se formatea con el `schema`.

## Reparto por requerimiento

| Req | Router | Service | Tests |
|---|---|---|---|
| 1 Registrar | `routers/auth.py` | `services/auth_service.py` + `core/security.py` | `unit/test_auth_service`, `unit/test_security`, `api/test_auth_api` |
| 2 Login | `routers/auth.py` | `services/auth_service.py` + `core/security.py` + `core/deps.py` | idem |
| 3 Crear jugador de club | `routers/club_players.py` | `services/club_player_service.py` | `unit/test_club_player_service`, `api/test_club_players_api` |
| 4 Listar comportamientos | `routers/behaviors.py` | `services/behavior_service.py` + `behaviors/` | `unit/test_behavior_service`, `unit/test_default_behaviors`, `api/test_behaviors_api` |
| 5 Detalle comportamiento | `routers/behaviors.py` | `services/behavior_service.py` | idem |
| 6 Crear liga | `routers/leagues.py` | `services/league_service.py` | `unit/test_league_service`, `api/test_leagues_api` |
| 7 Listar ligas | `routers/leagues.py` | `services/league_service.py` | idem |
| 8 Unirse a liga | `routers/leagues.py` | `services/league_service.py` | idem |
| 9 Abandonar liga | `routers/leagues.py` | `services/league_service.py` | idem |
| 10 Lobby de liga | `routers/leagues.py` + `routers/ws.py` | `services/league_service.py` | idem |
| 11 Crear amistoso | `routers/friendlies.py` | `services/friendly_service.py` | `unit/test_friendly_service`, `api/test_friendlies_api` |
| 12 Listar amistosos | `routers/friendlies.py` | `services/friendly_service.py` | idem |
| 13 Unirse a amistoso | `routers/friendlies.py` | `services/friendly_service.py` | idem |
| 14 Iniciar partido | `routers/friendlies.py` | `services/friendly_service.py` + `engine/match_engine.py` | idem + `unit/test_match_engine` |
| 15 Ejecutar comportamiento | (no es endpoint) | `engine/match_engine.py` + `behaviors/` | `unit/test_match_engine`, `unit/test_default_behaviors` |
| 16 Estado del partido | `routers/matches.py` + `routers/ws.py` | `services/match_service.py` + `core/ws_manager.py` | `api/test_matches_api` |

## Cómo se trabaja

1. Cada uno toma un requerimiento y crea una rama: `git checkout -b feature/req-08-unirse-liga`
2. Implementa el `raise NotImplementedError(...)` del service correspondiente (los comentarios dicen qué va adentro).
3. Saca el `skip` de los tests de ese requerimiento y los hace pasar.
4. Pull request a `main`.

Mientras algo no esté implementado, el endpoint responde **501** (no rompe el servidor).

## Pendientes de definir con el equipo / enunciado

- Atributos de un jugador de club (`models/club_player.py`).
- Cantidad de participantes de un amistoso y de una liga.
- Interfaz exacta de la API de comportamientos (`behaviors/base.py`).
- Condición de fin y velocidad del partido (`engine/match_engine.py`).
