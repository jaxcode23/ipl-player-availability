# 🏏 IPL Player Availability

> **Component 7** of the **IPL Championship Prediction System** — a deterministic ETL pipeline that collects cricket news, extracts player availability events (injuries, recoveries, replacements, suspensions), normalizes player identities, and stores structured historical data for downstream match prediction.

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite)
![Pytest](https://img.shields.io/badge/Tests-400%2B-success?style=for-the-badge)
![Ruff](https://img.shields.io/badge/Lint-Ruff-purple?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

---

# 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Architecture](#-architecture)
- [ETL Workflow](#-etl-workflow)
- [Project Structure](#-project-structure)
- [Database Schema](#-database-schema)
- [Quick Start](#-quick-start)
- [Development](#-development)
- [Pipeline Performance](#-pipeline-performance)
- [Project Status](#-project-status)
- [Roadmap](#-roadmap)
- [Documentation](#-documentation)
- [Design Principles](#-design-principles)

---

# 📌 Overview

Player availability is one of the strongest indicators influencing match outcomes in T20 cricket. This component continuously monitors trusted cricket news sources, detects player availability updates, normalizes player identities, and stores structured availability events for downstream analytics and prediction models.

The pipeline is **fully deterministic**, relying exclusively on rule-based extraction, alias resolution, and database lookups—**no machine learning, LLMs, or embeddings are used**.

---

# ✨ Features

- 🔄 Automated RSS-based cricket news collection
- 🩹 Injury, recovery, replacement and suspension extraction
- 🏏 Canonical player & team normalization
- 🔗 Alias registry with collision detection
- 📊 Historical availability event storage
- ⚡ Deterministic ETL pipeline
- 🧪 400+ automated tests
- 🗄️ SQLite database backend
- 📦 Modular architecture with clear separation of concerns
- 🛠️ Production-quality formatting & linting using Ruff

---

# 🛠 Technology Stack

| Layer | Technology |
|--------|------------|
| Language | Python 3.12 |
| Database | SQLite |
| ORM | SQLAlchemy 2 |
| Validation | Pydantic v2 |
| HTTP Client | httpx |
| Feed Parsing | feedparser |
| Testing | pytest |
| Linting | Ruff |
| Formatting | Ruff Format |

---

# 🏗 Architecture

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
                           Parsed Availability Record
                                       │
                                       ▼
                    ┌──────────────────────────────────┐
                    │     Normalization Layer          │
                    │ Alias Registry • Validation      │
                    │ Canonical Player & Team Names    │
                    └─────────┬────────────────────────┘
                              │
                              ▼
                        Database Resolver
                              │
                              ▼
                      SQLite Event Repository
```

---

# 🔄 ETL Workflow

| Stage | Responsibility |
|--------|----------------|
| **Collect** | Fetch RSS feeds from cricket news sources |
| **Parse** | Extract availability events using deterministic regex rules |
| **Normalize** | Canonicalize player and team names |
| **Resolve** | Match players against the SQLite database |
| **Store** | Persist structured availability events |

---

# 📂 Project Structure

```text
player_availability/
│
├── collectors/          # RSS & HTTP collectors
├── parsers/             # Rule-based extraction engine
├── normalizers/         # Canonical name normalization
├── db/                  # Models, repository & resolver
├── pipeline/            # ETL orchestration
├── domain/              # Domain models
├── tests/               # Unit & integration tests
└── docs/                # Project documentation
```

---

# 🗄 Database Schema

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

# 🚀 Quick Start

## Installation

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -e .

cp .env.example .env
```

Initialize the database:

```bash
python -m player_availability init-db
```

Run the live pipeline:

```bash
python -m player_availability run-pipeline
```

Run with mock data:

```bash
python -m player_availability run-pipeline --use-mock
```

Insert a manual event:

```bash
python -m player_availability add-event --player-id 1 --event-type injury
```

---

# 💻 Development

```bash
ruff check .

ruff format .

pytest -v

pytest -v -k pipeline
```

---

# 📈 Pipeline Performance

| Metric | Value |
|---------|------:|
| Articles Collected | 151 |
| Records Parsed | 111 |
| Records Normalized | 71 |
| Players Resolved | 17 |
| Events Stored | 17 |
| Remaining Unresolved | 54 |
| Automated Tests | **400 Passing** |

Example pipeline execution:

```text
151 Articles
      │
      ▼
111 Parsed Records
      │
      ▼
71 Normalized Records
      │
      ▼
17 Player Matches
      │
      ▼
17 Stored Availability Events
```

> Remaining unresolved records are resolver-side limitations (exact-match lookups and stale database state), not parser failures.

---

# 📊 Project Status

| Module | Status |
|----------|--------|
| RSS Collectors | ✅ Complete |
| Parser Engine | ✅ Complete |
| Player Normalization | ✅ Complete |
| Alias Registry | ✅ Complete |
| Database Layer | ✅ Complete |
| Pipeline Integration | ✅ Complete |
| Test Suite | ✅ 400 Passing |
| Documentation | ✅ Complete |
| Resolver Enhancements | 🚧 In Progress |

---

# 🛣 Roadmap

- [x] RSS Feed Collection
- [x] Rule-Based Parsing Engine
- [x] Alias Registry
- [x] SQLite Storage
- [x] Automated Testing
- [ ] Advanced Resolver Strategies
- [ ] PostgreSQL Support
- [ ] Incremental ETL Execution
- [ ] Monitoring Dashboard
- [ ] REST API Integration

---

# 📚 Documentation

Additional project documentation is available in the **docs/** directory.

| File | Description |
|------|-------------|
| `README.md` | Project overview |
| `AGENTS.md` | Developer onboarding guide |
| `architecture_review.md` | Architecture and design review |

---

# 🎯 Design Principles

- Deterministic over probabilistic
- No machine learning or LLM dependencies
- Modular ETL architecture
- High test coverage
- Clean separation of responsibilities
- Maintainable and extensible codebase
- Production-quality engineering practices

---

## ⭐ Component Summary

This component provides a **deterministic, production-ready ETL pipeline** for IPL player availability tracking. By combining automated news collection, rule-based extraction, canonical normalization, and structured persistence, it produces reliable historical availability data for use in AI-powered IPL match prediction systems.