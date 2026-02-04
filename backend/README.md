# Backend Local Development

## Prerequisites
- Python 3.10+
- pip

## Directory Structure (Depth 2)
```
backend/
  app/
    api/
    db/
    models/
    schemas/
    services/
    data_providers/
    ml/
    config.py
    main.py
  data/
  requirements.txt
  start.py
  venv/
```

## Local Setup
1. `cd backend`
2. `python -m venv venv`
3. `source venv/bin/activate`
4. `pip install -r requirements.txt`
5. `cp ../.env.example .env`
6. `mkdir -p data`

## Run
- `python start.py`
- Default port: `8888`

## Verify
```
NO_PROXY=127.0.0.1,localhost curl -i http://127.0.0.1:8888/health
```

## Common Issues
- `Address already in use` -> stop the existing process on port `8888`.
- `HTTP 502` on health check -> your proxy intercepted localhost; use `NO_PROXY` as above.
- `unable to open database file` -> ensure `backend/data/` exists.
