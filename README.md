# Pokemon Ability API — Technical Test Documentation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Requirements Overview](#2-requirements-overview)
3. [Technology Stack](#3-technology-stack)
4. [Project Structure](#4-project-structure)
5. [Architecture](#5-architecture)
6. [Database Schema](#6-database-schema)
7. [API Documentation](#7-api-documentation)
8. [Setup & Installation](#8-setup--installation)
9. [Configuration](#9-configuration)
10. [Testing](#10-testing)
11. [Implementation Details](#11-implementation-details)
12. [Appendix](#12-appendix)

---

## 1. Executive Summary

This project implements a FastAPI-based web service that receives a JSON payload containing user identifiers and a Pokemon ability ID, fetches ability data from the external [PokeAPI](https://pokeapi.co/), normalizes the nested `effect_entries` field, persists the data to a MySQL database, and returns an enriched JSON response including the list of Pokemon that can possess the ability.

The solution is fully containerized using Docker Compose, with separate services for the FastAPI application and the MySQL database. The application follows a layered architecture (Routes → Controllers → Models/DB) with clear separation of concerns, centralized logging, and environment-based configuration.

---

## 2. Requirements Overview

### Original Requirements

Build a FastAPI framework in Python 3.9+ that can:

1. Receive an input JSON and parse the data inside it
2. Hit the `pokemon_ability_id` against `https://pokeapi.co/api/v2/ability/{pokemon_ability_id}`
3. Normalize the `effect_entries` dict from the response
4. Store the normalized `effect_entries` in a database (MySQL, PostgreSQL, or SQLite)
5. Return the row(s) as JSON including `raw_id`, `user_id`, and the list of Pokemon names that can have the ability
6. Validate `raw_id` (string + int, 13 chars) and `user_id` (int, 7 chars)
7. **Plus point:** Containerize both the FastAPI service and the database

---

## 3. Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Language | Python | 3.11 | Runtime |
| Web Framework | FastAPI | 0.115.0 | REST API framework |
| ASGI Server | Uvicorn | 0.32.0 | Production server |
| Validation | Pydantic | 2.9.2 | Request/response schemas |
| ORM | SQLAlchemy | 2.0.35 | Database abstraction |
| DB Driver | PyMySQL | 1.1.1 | MySQL connectivity |
| HTTP Client | httpx | 0.27.2 | Async external API calls |
| Config | python-dotenv | 1.0.1 | Env variable loading |
| Database | MySQL | 8.0 | Data persistence |
| Containerization | Docker & Compose | 27.5.1 & v2.32.4-desktop.1 | Deployment |

### Why These Choices?

- **SQLAlchemy** : Mature ORM with connection pooling, works with any relational database
- **MySQL 8.0** : Stable LTS, widely supported, integrated into existing ecosystems
- **Docker Compose** : Multi-service orchestration

---

## 4. Project Structure

```
pokemon-api/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entrypoint
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── controller.py            # Business logic orchestration
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py              # DB engine, session, init
│   ├── models/
│   │   ├── __init__.py
│   │   └── model.py                 # SQLAlchemy ORM model
│   ├── routes/
│   │   ├── __init__.py
│   │   └── router.py                # API endpoint definitions
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schema.py                # Pydantic request/response
│   └── utils/
│       ├── __init__.py
│       ├── config.py                # Settings from .env
│       └── logger.py                # Centralized log setup
├── .dockerignore
├── .env                             # Environment variables
├── Dockerfile                       # API container build
├── docker-compose.yml               # Multi-service orchestration
├── requirements.txt                 # Python dependencies
├── pokemon-api.postman_collection.json
└── README.md
```

### Layer Responsibilities

| Layer | Responsibility | Example File |
|---|---|---|
| Routes | HTTP endpoint definitions, dependency injection | `router.py` |
| Controllers | Business logic | `controller.py` |
| Models | Database table structure | `model.py` |
| Schemas | Input/output data contracts | `schema.py` |
| DB | Connection & session management | `database.py` |
| Utils | Cross-cutting concerns (config, logging) | `config.py`, `logger.py` |

---

## 5. Architecture

### Request Flow

<img width="1063" height="271" alt="flip drawio (2)" src="https://github.com/user-attachments/assets/13773c25-e099-4d02-9084-f7227473bc2e" />

The application orchestrates a simple request-response pattern across four components. The client sends a POST request to the API Service, which fetches ability data from the external PokeAPI, normalizes it, and persists the result to MySQL before returning the final JSON response. The API Service acts as the central coordinator — calling PokeAPI for raw data and writing to MySQL for persistence.

Four components, each with a single responsibility:

- **Client** — Any HTTP client that sends JSON payloads and consumes the response.
- **API Service** — FastAPI application combining routing, validation, and business logic. Handles request routing, Pydantic input validation, external API orchestration, data normalization, and database persistence.
- **PokeAPI** — External public data source (`https://pokeapi.co/api/v2`).
- **MySQL** — Persistent storage.

### Sequence Diagram

<img width="728" height="777" alt="Screenshot 2026-04-18 at 22 30 30" src="https://github.com/user-attachments/assets/38d5565a-a9a8-4295-ad4b-f26524f477cc" />

The sequence diagram shows how components interact during a single request:

1. **Client → API Service:** Client sends `POST /pokemon/ability` with the JSON payload.
2. **API Service:** Validates input via Pydantic (`raw_id` length, `user_id` format).
3. **API Service → PokeAPI:** API Service makes an async HTTP GET to `/ability/{id}`.
4. **PokeAPI → API Service:** PokeAPI returns the ability data, including `effect_entries` and `pokemon` list.
5. **API Service → MySQL:** API Service normalizes `effect_entries` and inserts them within a single transaction.
6. **MySQL → API Service:** Database confirms commit.
7. **API Service → Client:** API Service builds and serializes the response, returning `200 OK` with the enriched JSON.



---

## 6. Database Schema

### Table: `pokemon_abilities`

| Column | Type | Nullable | Index | Description |
|---|---|---|---|---|
| `id` | INT | NO | PRIMARY | Auto-increment surrogate key |
| `raw_id` | VARCHAR(13) | NO | YES | 13-char identifier from input |
| `user_id` | BIGINT | NO | YES | 7-digit user ID from input |
| `pokemon_ability_id` | INT | NO | YES | PokeAPI ability ID |
| `effect` | TEXT | YES | - | Full effect description |
| `language` | TEXT | YES | - | JSON string `{"name": ..., "url": ...}` |
| `short_effect` | TEXT | YES | - | Short effect summary |
| `created_at` | DATETIME | NO | - | Auto-set on insert |

### DDL

```sql
CREATE TABLE pokemon_abilities (
  id INT AUTO_INCREMENT PRIMARY KEY,
  raw_id VARCHAR(13) NOT NULL,
  user_id BIGINT NOT NULL,
  pokemon_ability_id INT NOT NULL,
  effect TEXT,
  language TEXT,
  short_effect TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_raw_id (raw_id),
  INDEX idx_user_id (user_id),
  INDEX idx_ability_id (pokemon_ability_id)
);
```

### Sample Data

After calling the endpoint with `pokemon_ability_id=150`, the following rows are stored

```
id | raw_id         | user_id | ability_id | language                                      | short_effect
1  | 7dsa8d7sa9dsa  | 5199434 | 150        | {"name": "fr", "url": "...language/5/"}       | Se transforme en entrant au combat.
2  | 7dsa8d7sa9dsa  | 5199434 | 150        | {"name": "de", "url": "...language/6/"}       | Verwandelt sich beim Betreten des Kampfes...
3  | 7dsa8d7sa9dsa  | 5199434 | 150        | {"name": "en", "url": "...language/9/"}       | Transforms upon entering battle.
```

---

## 7. API Documentation

### Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check for container orchestration |
| POST | `/pokemon/ability` | Fetch, normalize, and store Pokemon ability data |
| GET | `/docs` | Auto-generated Swagger UI |

### POST /pokemon/ability

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "raw_id": "7dsa8d7sa9dsa",
  "user_id": "5199434",
  "pokemon_ability_id": "150"
}
```

**Request Schema:**

| Field | Type | Constraint | Description |
|---|---|---|---|
| `raw_id` | string | exactly 13 chars | Random string+int identifier |
| `user_id` | string/int | 7-digit integer | User identifier |
| `pokemon_ability_id` | string/int | integer | PokeAPI ability ID |

**Success Response (200 OK):**
```json
{
    "raw_id": "7dsa8d7sa9dsa",
    "user_id": 5199434,
    "returned_entries": [
        {
            "effect": "Ce Pokémon se transforme en un adversaire aléatoire en entrant au combat.  Cet effet est identique à la capacité transform.",
            "language": {
                "name": "fr",
                "url": "https://pokeapi.co/api/v2/language/5/"
            },
            "short_effect": "Se transforme en entrant au combat."
        },
        {
            "effect": "Pokémon mit dieser Fähigkeit kopieren einen zufälligen Gegner. Der Effekt ist identisch mit transform.",
            "language": {
                "name": "de",
                "url": "https://pokeapi.co/api/v2/language/6/"
            },
            "short_effect": "Verwandelt sich beim Betreten des Kampfes in den Gegner."
        },
        {
            "effect": "This Pokémon transforms into a random opponent upon entering battle.  This effect is identical to the move transform.",
            "language": {
                "name": "en",
                "url": "https://pokeapi.co/api/v2/language/9/"
            },
            "short_effect": "Transforms upon entering battle."
        }
    ],
    "pokemon_list": [
        "ditto"
    ]
}
```

**Error Responses:**

| Status | Scenario | Example |
|---|---|---|
| 422 | Validation failure (raw_id length, user_id format) | `{"detail": [{"msg": "raw_id must be exactly 13 characters"}]}` |
| 404 | Ability not found in PokeAPI | `{"detail": "Pokemon ability id 99999 not found"}` |
| 502 | PokeAPI unreachable | `{"detail": "Failed to reach PokeAPI: ..."}` |
| 500 | Database persistence error | `{"detail": "Database persistence error"}` |

### Swagger UI

<img width="1710" height="949" alt="Screenshot 2026-04-18 at 21 52 27" src="https://github.com/user-attachments/assets/0279a4e4-529c-4e1b-bcb9-b4d00706cdb6" />

---

## 8. Setup & Installation

### Prerequisites

- Docker Desktop (or Docker Engine) — version 27.5.1
- Docker Compose — version v2.32.4-desktop.1
- Git
- - Python 3.11+

### Start Full Docker

1. **clone the project:**
   ```bash
   git clone https://github.com/zildirayalfirli/pokemon-api.git
   cd pokemon-api
   ```

2. **Review `.env` configuration** :
   ```bash
   cat .env
   ```

3. **Build and start containers:**
   ```bash
   docker compose up -d --build
   ```

4. **Verify health:**
   ```bash
   curl http://localhost:4400/health
   # Expected: {"status":"healthy"}
   ```

### Alternative: Local Dev + DB in Docker

1. **Start only MySQL:**
   ```bash
   docker compose up -d mysql
   ```

2. **Setup Python venv:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Update `.env` — change `DB_HOST=mysql` to `DB_HOST=localhost`**

4. **Run with auto-reload:**
   ```bash
   python -m app.main 
   ```

---

## 9. Configuration

All configuration is loaded from the `.env` file via `python-dotenv`.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MYSQL_ROOT_PASSWORD` | - | Root password for MySQL container |
| `MYSQL_DATABASE` | - | Database name |
| `MYSQL_USER` | - | Application DB user |
| `MYSQL_PASSWORD` | - | Password for application user |
| `DB_HOST` | `mysql` | DB host |
| `DB_PORT` | `3306` | DB port |
| `DB_USER` | (same as `MYSQL_USER`) | App connects as this user |
| `DB_PASSWORD` | (same as `MYSQL_PASSWORD`) | App connects with this password |
| `DB_NAME` | (same as `MYSQL_DATABASE`) | Database to connect to |
| `POKEAPI_BASE_URL` | `https://pokeapi.co/api/v2` | External API base URL |
| `POKEAPI_TIMEOUT` | `10.0` | Request timeout (seconds) |
| `HOST` | `0.0.0.0` | Uvicorn bind host |
| `PORT` | `4400` | Uvicorn bind port |
| `WORKERS` | `4` | Number of Uvicorn workers |

---

## 10. Testing

### Test Scenarios

The following scenarios were validated using Postman:

#### Scenario 1: Happy Path — Ability 150

**Request:**
```json
POST http://localhost:4400/pokemon/ability
{
  "raw_id": "7dsa8d7sa9dsa",
  "user_id": "5199434",
  "pokemon_ability_id": "150"
}
```

**Result:** 200 OK, 3 entries returned, `pokemon_list: ["ditto"]`

<img width="870" height="620" alt="Screenshot 2026-04-18 at 22 58 07" src="https://github.com/user-attachments/assets/13b17d4c-570b-4b57-ae67-90269ae0f934" />

#### Scenario 2: Ability with Multiple Pokemon — Ability 65

**Request:**
```json
{
  "raw_id": "abc12345fg678",
  "user_id": "1234567",
  "pokemon_ability_id": "65"
}
```

**Result:** 200 OK, `pokemon_list` contains multiple Pokemon

<img width="829" height="608" alt="Screenshot 2026-04-18 at 22 55 57" src="https://github.com/user-attachments/assets/eea55116-5b81-4314-9d5b-5e7459354fc0" />

#### Scenario 3: Invalid raw_id Length

**Request:**
```json
{
  "raw_id": "short",
  "user_id": "5199434",
  "pokemon_ability_id": "150"
}
```

**Result:** 422 Unprocessable Entity, validation error

<img width="862" height="597" alt="Screenshot 2026-04-18 at 22 54 43" src="https://github.com/user-attachments/assets/b445771b-e54f-498d-a73c-835f3fdb4737" />


#### Scenario 4: Invalid user_id Format

**Request:**
```json
{
  "raw_id": "7dsa8d7sa9dsa",
  "user_id": "123",
  "pokemon_ability_id": "150"
}
```

**Result:** 422 — user_id must be 7-digit integer

<img width="847" height="591" alt="Screenshot 2026-04-18 at 22 54 11" src="https://github.com/user-attachments/assets/0a0186bf-0ae0-4e3d-b744-4781c4021cac" />

#### Scenario 5: Ability ID Not Found

**Request:**
```json
{
  "raw_id": "7dsa8d7sa9dsa",
  "user_id": "5199434",
  "pokemon_ability_id": "99999"
}
```

**Result:** 404 Not Found

<img width="853" height="401" alt="Screenshot 2026-04-18 at 22 53 36" src="https://github.com/user-attachments/assets/cd84d563-a234-4649-b948-47c95b293c06" />

### Database Verification

After running the test scenarios, data was verified in MySQL:

```sql
SELECT id, raw_id, user_id, pokemon_ability_id,
       LEFT(effect, 50) AS effect_preview,
       language,
       LEFT(short_effect, 40) AS short_effect_preview
FROM pokemon_abilities
ORDER BY id;
```

<img width="1298" height="636" alt="Screenshot 2026-04-18 at 22 58 44" src="https://github.com/user-attachments/assets/ceb5fa49-5f6d-4685-bc14-135de9060861" />

---

## 11. Implementation Details

### Input Validation

Defined in `app/schemas/schema.py`:

- `raw_id` — must be exactly 13 characters (string)
- `user_id` — coerced from string to int, must be 7 digits (1,000,000–9,999,999)
- `pokemon_ability_id` — coerced from string to int

### Data Normalization

The raw PokeAPI response contains `effect_entries` as a nested list:

```json
"effect_entries": [
  {"effect": "...", "language": {...}, "short_effect": "..."},
  ...
]
```

Each entry is stored as a separate row in `pokemon_abilities`. This flattens the hierarchy and makes SQL queries straightforward.

### Logging

Centralized setup in `app/utils/logger.py`:

- Format: `timestamp | level | module | message`
- Each module uses `logging.getLogger(__name__)` for contextual names
- Third-party loggers (`httpx`, `sqlalchemy.engine`) quieted to WARNING

### Worker Model

Uvicorn spawns 4 worker processes by default (configurable via `WORKERS` env var). Each worker:

- Runs the full FastAPI app independently
- Maintains its own DB connection pool
- Handles requests in parallel

This enables concurrent request handling without I/O blocking.

---

## 12. Appendix

### A. Sample cURL Commands

```bash
# Health check
curl http://localhost:4400/health

# Main endpoint
curl -X POST http://localhost:4400/pokemon/ability \
  -H "Content-Type: application/json" \
  -d '{
    "raw_id": "7dsa8d7sa9dsa",
    "user_id": "5199434",
    "pokemon_ability_id": "150"
  }'
```

### B. Postman Collection

The Postman collection has been exported and included in the repository as `pokemon-api.postman_collection.json`. Import this file into Postman to access pre-configured requests for all available endpoints.

---
