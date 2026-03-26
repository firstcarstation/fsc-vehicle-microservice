# fsc-vehicle-microservice

Vehicle microservice scaffold based on the user service template. PostgreSQL database `vehicle_db`. Dependencies managed with [uv](https://github.com/astral-sh/uv).

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- PostgreSQL

## Setup

1. **Virtual environment and install**

```bash
uv venv
uv sync
```

2. **Environment**

```bash
cp .env.example .env
```

Set `DATABASE_URL` (e.g. `postgresql+psycopg2://user:password@localhost:5432/vehicle_db`) and `JWT_SECRET_KEY`.

## Database

Create the database and run migrations:

```bash
createdb vehicle_db
uv run alembic upgrade head
```

## Run

```bash
uv run uvicorn app.main:app --reload
```

API base: `http://127.0.0.1:8000`. Docs: `http://127.0.0.1:8000/docs`.

## Add dependency

```bash
uv add <package_name>
```

Commit `pyproject.toml` and `uv.lock`.

## Repository structure

```
fsc-vehicle-microservice/
├── app/
│   ├── main.py
│   ├── api/api_v1/routes.py, endpoints/
│   ├── core/ (config, logging, database, exceptions)
│   ├── models/ (vehicles, vehicle_images, vehicle_documents, vehicle_status_logs, enums)
│   ├── schemas/
│   ├── crud/command/, crud/query/
│   └── services/
├── alembic/ (env.py, script.py.mako, versions/)
├── tests/
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
└── README.md
```

## Schema (vehicle_db)

Core tables: **vehicles**, **vehicle_images**, **vehicle_documents**, **vehicle_status_logs**.

Relationships:
- `vehicles.user_id` references the User MS (external, no DB FK constraint)
- `vehicle_images.vehicle_id` -> `vehicles.vehicle_id`
- `vehicle_documents.vehicle_id` -> `vehicles.vehicle_id`
- `vehicle_status_logs.vehicle_id` -> `vehicles.vehicle_id`

Enums: `fuel_type_enum`, `vehicle_status_enum`, `vehicle_doc_enum`.
