# IPL Player Availability

> **Component 7** of the **IPL Championship Prediction System** — a deterministic ETL pipeline that continuously collects cricket news, extracts player availability events (injuries, recoveries, replacements, suspensions, withdrawals), normalizes player identities, and stores structured historical data for downstream match prediction and analytics.

---

# ✨ Features

- 🔄 Automated RSS-based cricket news collection
- 🩹 Deterministic extraction of player availability events
- 🏏 Canonical player & team normalization
- 🔗 Alias registry with collision detection
- 📊 Historical event storage using SQLite
- ⚡ Fully deterministic pipeline (no ML, LLMs, or embeddings)
- 🧪 400+ automated unit & integration tests
- 🏗️ Modular ETL architecture with clean separation of concerns
- 📦 Production-ready code quality with Ruff formatting & linting

---

# System Architecture

```text
                    python -m player_availability run-pipeline

                                  ┌────────────────────┐
                                  │  RSS Collectors    │
                                  │ ESPN • IPL • Mock │
                                  └─────────┬──────────┘
                                            │
                                            ▼
                               RawData (title, content, source)
                                            │
                                            ▼
                             ┌──────────────────────────┐
                             │      Rule Engine         │
                             │ Regex + Pattern Matching │
                             └─────────┬────────────────┘
                                       │
                                       ▼
                           ParsedRecord (raw extraction)
                                       │
                                       ▼
                    ┌──────────────────────────────────┐
                    │     Normalization Layer          │
                    │ Alias Registry • Validation      │
                    │ Canonical Player & Team Names    │
                    └─────────┬────────────────────────┘
                              │
                              ▼
                     Normalized Availability Event
                              │
                              ▼
                  ┌────────────────────────────────┐
                  │ Database Resolver & Repository │
                  │ SQLite + SQLAlchemy            │
                  └─────────┬──────────────────────┘
                            │
                            ▼
              Structured Availability History Database
```

---

# Technology Stack

| Layer | Technology |
|--------|------------|
| Language | Python 3.12 |
| ORM | SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Database | SQLite |
| HTTP Client | httpx |
| Feed Parsing | feedparser |
| Testing | pytest |
| Linting | Ruff |
| Formatting | Ruff Format |

---

# Project Structure

```text
player_availability/
│
├── collectors/          # RSS & news collectors
├── parsers/             # Deterministic extraction engine
├── normalizers/         # Canonical mapping & alias registry
├── db/                  # Database models & repository
├── pipeline/            # End-to-end ETL workflow
├── domain/              # Domain models
├── tests/               # Unit & integration tests
└── docs/                # Architecture & developer documentation
```

---

# ETL Workflow

1. **Collect** live RSS feeds from IPL and cricket news sources.
2. **Parse** articles using deterministic regex-based extraction.
3. **Normalize** player and team names using canonical alias mappings.
4. **Resolve** extracted players against the SQLite database.
5. **Store** validated availability events for downstream prediction models.

---

# Quick Start

## Installation

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Install dependencies
pip install -e .

# Configure environment
cp .env.example .env
```

---

## Initialize Database

```bash
python -m player_availability init-db
```

---

## Run Pipeline

### Live RSS

```bash
python -m player_availability run-pipeline
```

### Mock Dataset

```bash
python -m player_availability run-pipeline --use-mock
```

### Manual Event Entry

```bash
python -m player_availability add-event --player-id 1 --event-type injury
```

---

# Development

Run formatting, linting, and tests:

```bash
ruff check .

ruff format --check .

pytest -v

pytest -v -k pipeline
```

---

# Pipeline Performance

| Metric | Value |
|---------|------:|
| Articles Collected | 151 |
| Records Parsed | 111 |
| Records Normalized | 71 |
| Events Stored | 17 |
| Players Successfully Resolved | 17 |
| Players Unresolved | 54 |
| Automated Tests | **400 Passing** |

> The remaining unresolved records are resolver-side limitations (exact-match lookups and stale database state), not parser failures.

---

# Database Schema

## Teams

| Column |
|---------|
| id |
| name |
| short_code |
| created_at |

---

## Players

| Column |
|---------|
| id |
| name |
| team_id |
| role |
| is_foreign |
| created_at |

---

## Availability Events

| Column |
|---------|
| id |
| player_id |
| event_type |
| description |
| source_name |
| source_url |
| confidence |
| event_date |
| start_date |
| end_date |
| is_active |
| created_at |
| updated_at |

---

# Data Flow

```text
RSS Feed
   │
   ▼
Collector
   │
   ▼
Parser
   │
   ▼
Normalizer
   │
   ▼
Resolver
   │
   ▼
Repository
   │
   ▼
SQLite Database
```

---

# Project Status

| Module | Status |
|----------|--------|
| RSS Collectors | ✅ Complete |
| Parser Engine | ✅ Complete |
| Normalization | ✅ Complete |
| Alias Registry | ✅ Complete |
| Database Layer | ✅ Complete |
| ETL Pipeline | ✅ Complete |
| Testing | ✅ 400 Passing |
| Documentation | ✅ Complete |
| Resolver Optimisation | 🚧 Ongoing |

---

# Future Improvements

- Improve resolver for ambiguous player names
- Support additional RSS/news providers
- PostgreSQL backend support
- Incremental ETL execution
- JSON/CSV export utilities
- Pipeline monitoring dashboard
- Performance metrics & logging improvements

---

# Documentation

Additional documentation is available in the `docs/` directory.

| File | Description |
|------|-------------|
| `AGENTS.md` | Developer onboarding and architecture guide |
| `architecture_review.md` | Detailed architecture review and design decisions |
| `README.md` | Project overview and usage guide |

---

# Design Principles

- Deterministic over probabilistic
- No machine learning or LLM dependencies
- Clean separation of ETL stages
- Strong test coverage
- Maintainable and extensible architecture
- Production-quality code style
