# IPL Player Availability

**Component 7** of the IPL Championship Prediction System — a deterministic ETL pipeline that monitors cricket news, extracts player availability events (injuries, recoveries, replacements, suspensions), and persists structured historical data for downstream ML prediction.

## Architecture

```
python -m player_availability run-pipeline
        │
        ▼
  ┌─────────────────┐
  │   COLLECT       │  RSS feeds → RawData (title, content, source)
  │   (httpx + XML) │
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │   PARSE         │  Rule engine → ParsedRecord (player, team,
  │   (regex +      │  event type, injury, dates, confidence)
  │    proximity)   │
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │   NORMALIZE     │  AliasRegistry → NormalizedRecord
  │   (canonical    │  (canonical names, dedup, validation)
  │    mapping)     │
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │   MAP + STORE   │  DbPlayerResolver → EventCreate → SQLite
  │   (DB lookup)   │
  └─────────────────┘
```

Every layer is deterministic — no ML, no LLMs, no embeddings.

## Quick Start

```powershell
# Install
python -m venv .venv
.venv\Scripts\activate
pip install -e .
cp .env.example .env

# Init database
python -m player_availability init-db

# Run pipeline (live RSS)
python -m player_availability run-pipeline

# Run with mock data
python -m player_availability run-pipeline --use-mock

# Manual event entry
python -m player_availability add-event --player-id 1 --event-type injury
```

## Development

```powershell
ruff check .           # Lint
ruff format --check .  # Format check
pytest -v              # Run 400+ tests
pytest -v -k "pipeline"  # Integration tests only
```

## Pipeline Stats (baseline)

| Metric | Count |
|---|---|
| Raw articles collected | 151 |
| Records parsed | 111 |
| Records normalized | 71 |
| Events stored | 17 |
| Players resolved | 17 |
| Players unresolved | 54 |

The 54 unresolved are all resolver-side (players in seed + alias registry but DB resolver lookup fails, typically due to stale DB state or exact-match-only limitations). See `docs/` for the full architecture review and agent onboarding.

## Status

| Stage | Status |
|---|---|
| Collectors | ✅ Complete |
| Parsers | ✅ Complete (contamination fixed) |
| Normalizers | ✅ Complete |
| Resolver | ⚠️ Exact-match only — known bottleneck |
| Pipeline Integration | ✅ Complete |
| Tests | ✅ 400 passing, ruff clean |
