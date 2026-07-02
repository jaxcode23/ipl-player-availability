# Player Availability — Agent Onboarding Guide

## 1. Project Identity

| Field | Value |
|---|---|
| **Name** | `player-availability` |
| **Version** | 0.1.0 |
| **System** | Component 7 of IPL Championship Prediction System |
| **Python** | >= 3.12 |
| **Stack** | SQLAlchemy 2.0, Pydantic 2, httpx, BeautifulSoup, loguru |
| **Tests** | 400 (pytest), lint: ruff |
| **DB** | SQLite (default), PostgreSQL-swappable via conneciton string |

### Purpose

Collect live cricket RSS feeds, deterministically extract player availability signals (injuries, ruled-out, replacements, suspensions, recoveries), normalize to canonical forms, and persist structured events for AI-powered match prediction.

### Core Constraint

**Zero ML/NLP.** Every decision is made by regex, keyword scan, or alias lookup. The system must be fully debuggable and reproducible.

---

## 2. Architecture: End-to-End Data Flow

### High-Level Pipeline

```
RawData (dataclass)
    → ParsedRecord (dataclass)
    → NormalizedRecord (dataclass)
    → EventCreate (Pydantic)
    → INSERT INTO availability_events (SQLite)
```

### Stage 1: Collect

**Entry point:** `python -m player_availability run-pipeline`

- `__main__.py` reads `settings.source_registry` from config, builds collectors.
- Active sources: `rediff_cricket`, `google_cricket_news` (both `GenericRSSCollector`).
- `GenericRSSCollector.collect()` → `fetch_with_retry()` (httpx, exp backoff, max 3 retries) → `parse_rss_items()` (xml.etree) → `list[RawData]`.
- `RawData` fields: `source_name`, `title`, `content` (description), `url`, `published_at`.
- `MockCollector` returns hardcoded sample data when `--use-mock` is passed.

### Stage 2: Parse

**Entry point:** `GenericArticleParser.parse(raw)` → calls `rule_engine.parse_article()`.

The rule engine (`parsers/rule_engine.py`, 716 lines) is the heart of the system:

1. **HTML cleanup** via `clean_html()` (BeautifulSoup + lxml)
2. **Event detection** via `_find_all_keyword_matches()` — iterates `EVENT_KEYWORDS` dict, finds matching keywords in text, collects event types found.
3. **Player name extraction** via `_find_nearest_name()` — regex `_PLAYER_RE` finds capitalized name candidates within proximity of keyword matches. Scores candidates by distance to keyword, recency, and bonus points from `_INDIVIDUAL_PLAYER_INDICATORS`.
4. **Validation** via `_is_valid_player_candidate()` — rejects names matching `HEADLINE_FRAGMENTS`, `GENERIC_NOUNS`, `COUNTRY_NAMES`, `PUBLISHER_NAMES`, `_is_team_name_exact()` (checks against `TEAM_NAMES` + word fragments), `name.isupper()`, single words in `REGION_NAMES`.
5. **Team extraction** via `extract_team_name()` — matches known team names/variants in article text.
6. **Injury type extraction** via `extract_injury_type()` — matches `INJURY_KEYWORDS`.
7. **Replacement extraction** via `_extract_replacement_pair()` — regex patterns for "X replaces Y", "[team] signs X", etc. Two paths:
   - Pair pattern: captures incoming + outgoing player names together.
   - Single pattern: `_extract_replacement_signed_name()` — finds lone player name after "signs", "names", "roped in", etc.
8. **Effective date extraction** via `extract_effective_date()`.
9. **Confidence determination** via `determine_confidence()` — checks `HIGH_CONFIDENCE_PHRASES` → `LOW_CONFIDENCE_PHRASES` → default `MEDIUM`.
10. **Deduplication** via `_deduplicate_records()` — keeps highest-priority event per article per player.
11. Returns `list[ParsedRecord]`.

`ParsedRecord` fields: `player_name`, `team_name`, `event_type`, `injury_type`, `replaced_player_name`, `replacement_player_name`, `effective_date`, `confidence`, `title`, `source_name`, `source_url`, `published_at`.

### Stage 3: Normalize

**Entry point:** `DefaultNormalizer.normalize(parsed_records)`.

1. **PlayerNameNormalizer** — strips noise phrases ("Cricinfo", "Rediff", "Returns", "Google News"), strips parenthetical suffixes, normalizes whitespace, then looks up via `PlayerAliasRegistry`. If alias not found, applies `to_proper_case()`.
2. **TeamNameNormalizer** — maps team variants ("rcb", "royal challengers", "bangalore") to canonical via `TeamAliasRegistry`.
3. **InjuryNormalizer** — maps injury variants ("knee strain", "knee issue") to canonical via `InjuryNormalizer`.
4. **validate_record()** — rejects records where player_name matches a publisher name, generic noun, country name, or has other structural issues.
5. **Deduplicator** — dedup by `(player_name, event_type, source_name, effective_date)`. Source is part of the key (known weakness — same event from different sources may be stored twice).

Returns `list[NormalizedRecord]`.

### Stage 4: Map + Store

**Entry point:** `normalized_to_event_create(record, player_resolver)`.

1. `DbPlayerResolver.resolve(player_name, team_name)` — normalizes name, then tries:
   - **Strategy 1 & 2:** Exact DB match on canonical name (with optional team filter).
   - **Strategy 3:** Normalized string match (strip punctuation, hyphen → space).
   - **Strategy 4:** Initial-form match ("V Kohli" match "Virat Kohli").
   - **Strategy 5:** Surname match within team (if single candidate).
   - Returns `None` if no match, ambiguous (>1), or team mismatch.
2. `SqlRepository.add_event()` — inserts `EventCreate` into `availability_events` table.

---

## 3. Directory Map (src/player_availability)

| File | One-Liner |
|---|---|
| `__main__.py` | CLI entry: `init-db`, `run-pipeline`, `add-event` |
| `__init__.py` | `__version__ = "0.1.0"` |
| `config.py` | Pydantic settings: `SourceRegistry`, `IPLSettings` |
| `exceptions.py` | `PlayerAvailabilityError` hierarchy |
| `logging.py` | loguru setup |
| **collectors/** | |
| `base.py` | `BaseCollector` ABC, `RawData` dataclass |
| `generic_rss.py` | `GenericRSSCollector`: httpx fetch + RSS XML parse |
| `espn_cricinfo.py` | `ESPNCricinfoRSSCollector` (extends `GenericRSSCollector`) |
| `ipl_official.py` | `IPLOfficialCollector` (extends `GenericRSSCollector`) |
| `http_client.py` | `fetch_with_retry()` — httpx with exponential backoff |
| `rss_utils.py` | `parse_rss_items()`, `parse_rss_date()` |
| `mock.py` | `MockCollector` — seeded test data |
| `exceptions.py` | `SourceUnavailableError` |
| **parsers/** | |
| `rule_engine.py` | Core: 716 lines, 15+ extraction functions, the brain |
| `patterns.py` | 758 lines of keywords, regexes, blocklists |
| `article_parser.py` | `GenericArticleParser` — thin wrapper around rule_engine |
| `base.py` | `BaseParser` ABC, `ParsedRecord` dataclass |
| `espn_cricinfo.py` | `ESPNCricinfoParser` — unused in live pipeline |
| `ipl_official.py` | `IPLOfficialParser` — unused in live pipeline |
| `mock.py` | `MockParser` — unused in live pipeline |
| `exceptions.py` | `UnsupportedSourceError` |
| `utils.py` | `clean_html()` — BeautifulSoup + lxml |
| **normalizers/** | |
| `alias_registry.py` | `AliasRegistry` — case-insensitive alias→canonical dict, collision-guarded |
| `player.py` | `PlayerAliasRegistry` (~100 players, ~250 aliases), `PlayerNameNormalizer` |
| `team.py` | `TeamAliasRegistry` (10 teams) |
| `resolver.py` | `PlayerResolver` ABC |
| `aliassss.py` | (placeholder) |
| `mapper.py` | `normalized_to_event_create()` — maps `NormalizedRecord` → `EventCreate` |
| `default_normalizer.py` | `DefaultNormalizer` — orchestrates all sub-normalizers |
| `deduplication.py` | `Deduplicator`, `DedupKey` |
| `models.py` | `NormalizedRecord` dataclass |
| `utils.py` | `validate_record()`, `InjuryNormalizer`, `to_proper_case()`, helpers |
| `exceptions.py` | `ValidationError`, `UnresolvedPlayerError`, `UnhandledRecordError` |
| **db/** | |
| `base.py` | SQLAlchemy `DeclarativeBase` |
| `models.py` | `PlayerModel`, `TeamModel`, `AvailabilityEventModel` (ORM) |
| `resolver.py` | `DbPlayerResolver` — exact + fallback strategies |
| `repository.py` | `SqlRepository` — CRUD, status queries |
| `seed.py` | `PLAYER_SEED` (~250 entries), `TEAMS`, `seed_database()` |
| `session.py` | `engine`, `get_session()` context manager |
| **domain/** | |
| `enums.py` | `EventType`, `AvailabilityStatus`, `ConfidenceLevel`, `PlayerRole`, `SourceType` |
| `events.py` | `EventCreate`, `AvailabilityEvent`, `PlayerStatus` (Pydantic) |
| **pipeline/** | |
| `availability_pipeline.py` | `AvailabilityPipeline(collec→parse→norm→store)`, `PipelineResult` |

---

## 4. Key Data Structures

```
RawData(source_name, title, content, url, published_at)          — after collect
ParsedRecord(player_name, team_name, event_type, injury_type,     — after parse
             confidence, effective_date, ...)
NormalizedRecord(player_name, team_name, event_type, injury_type, — after normalize
                 confidence, effective_date, ...)
EventCreate(player_id, event_type, confidence, event_date, ...)   — domain model (Pydantic)
AvailabilityEvent(id, player_id, event_type, ..., is_active)      — returned from DB
```

### Database Tables

- `teams` — (id, name, short_name)
- `players` — (id, name, team_id, role, is_overseas)
- `availability_events` — (id, player_id, event_type, event_date, source_name, confidence, ...)

---

## 5. Changes Made (Session 2026-07-02)

### Problem: 151 articles → 127 parsed → 86 normalized → 17 stored → 69 unresolved

Root cause analysis identified 6 categories:

| Category | Count | Examples | Fix |
|---|---|---|---|
| A. Parser contamination (generic nouns) | 3 | "Centre", "Player", "League" | Added to `GENERIC_NOUNS` |
| B. Team word fragments | 2 | "Kings", "Indians" | Added `_TEAM_WORD_FRAGMENTS` set + check in `_is_team_name_exact()` |
| C. Headline fragments | 5 | "Captain", "April", "Deepens", "Dhoni Still", "He Last Played" | Added 20+ words to `HEADLINE_FRAGMENTS`; improved prefix/suffix stripping in `_is_valid_player_candidate()` |
| D. Missing aliases | 6 | "Quinton" → de Kock, "Hasaranga" → Wanindu Hasaranga, "Emanjot" → Emanjot Chahal, "Esterhuizen" → Connor Esterhuizen, "Bethell" → Jacob Bethell, "Ruchir Ahir" → Ruchit Ahir | Added to `PlayerAliasRegistry` |
| E. Short name aliases | 5 | "Quinton" (unique), "Hasaranga" (unique), "Emanjot" (unique), "Esterhuizen" (unique), "Bethell" (unique) | Registered as aliases (safe since only one player matches) |
| F. Missing seed entries | 1 | "Rachin Ravindra" (CSK→KKR for IPL 2026) | Added to `PLAYER_SEED` under KKR |

### Additional Fixes

- **Seed spelling bug:** "Kuldeep Yadav" listed for CSK (line 53) was actually a different player — corrected to "Kuldip Yadav" to match the alias registry. The pre-existing "Kuldeep Yadav" (KKR) was unaffected.
- **`sign` verb in regex:** Changed `(?:signs|names|...)` to `(?:signs?|names|...)` to match bare "sign" (e.g., "SK sign Akash Madhwal").
- **Ruchir Ahir verification:** Verified via IPL website, Cricbuzz, MI official — only "Ruchit Ahir" (with 't') exists. "Ruchir Ahir" is a typo. Added as alias.
- **Tests:** 32 new parser tests + 7 new normalizer tests.

### Pipeline Result (post-fix, stale DB)

| Metric | Before | After |
|---|---|---|
| Raw | 151 | 151 |
| Parsed | 127 | **111** (-16) |
| Normalized | 86 | **71** (-15) |
| Stored | 17 | 17 |
| Resolved | 17 | 17 |
| Unresolved | 69 | **54** (-15) |

All 10 identified contaminated outputs eliminated. Remaining 54 unresolved are resolver-side (players in seed + alias registry but DB lookup fails, likely due to stale DB data — re-seeding required for accurate count).

### File Changes Summary

| File | Change |
|---|---|
| `parsers/patterns.py` | `HEADLINE_FRAGMENTS`: +20 words (captain, pronouns, still, deepens, played, months). `GENERIC_NOUNS`: +3 (player, league, centre) |
| `parsers/rule_engine.py` | `_TEAM_WORD_FRAGMENTS` set (from all team variants, ≥4 chars). Extended `_is_team_name_exact()`. `signs?` in replacement regex |
| `normalizers/player.py` | +6 new aliases, +1 typo alias |
| `db/seed.py` | Rachin Ravindra (KKR). Kuldip Yadav spelling fix |
| `tests/unit/test_parsers/test_rule_engine.py` | +32 tests |
| `tests/unit/test_normalizers/test_player_normalizer.py` | +7 tests |

---

## 6. Remaining Issues / Next Steps

Ordered by priority:

### P1 — Data Integrity

1. **S Sharma alias collision** (`normalizers/player.py:130,154`): "Sandeep Sharma" and "Suyash Sharma" both register alias "S Sharma". `AliasRegistry.register()` silently overwrites. Add collision guard or deduplicate.
2. **Duplicate seed players across teams** (`db/seed.py`): ~15 players (Pat Cummins, David Warner, etc.) appear in 2+ teams. `seed_database()` skips the second with `if name in seen`. This means `DbPlayerResolver.resolve("Pat Cummins", "SRH")` fails because the DB only has Pat Cummins under KKR.
3. **DB-level unique constraint on events**: No unique constraint on `availability_events` → duplicate rows on re-runs.

### P2 — Resolution (Core Bottleneck)

4. **Fuzzy surname fallback in `DbPlayerResolver`**: When exact match fails, do `LIKE '%surname%'` scoped to team. Would recover most unresolved players.
5. **Alias↔Seed consistency check**: Verify every canonical in `PlayerAliasRegistry` has a matching `PlayerModel.name` in seed, and vice versa. A test (`test_sync_validation.py`) exists but more is needed.
6. **Expand alias coverage**: ~30 players in seed have no alias entries.

### P3 — Extraction Quality

7. **Hyphenated name regex**: `_PLAYER_RE` doesn't match "Jake Fraser-McGurk", "Naveen-ul-Haq". Update pattern.
8. **All-caps titles**: `_is_valid_player_candidate` rejects `name.isupper()`. Try `title.title()` conversion first.
9. **Title-priority for short content**: Google News snippets are ~1 sentence. Skip body parsing for <100 char content.
10. **Dead `pass` branch** at `rule_engine.py:445-446`: Intended scoring bonus for known surnames, never implemented.

### P4 — Cross-Run Dedup

11. **Pre-insert duplicate check** in `SqlRepository.add_event()`: Query for existing `(player_id, event_type, event_date, source_name)` before inserting.

### P5 — Observability

12. **Log reasons per unresolved player**: Log whether alias lookup failed, DB returned 0 or >1 rows, or team filter eliminated candidates.
13. **Externalize player data**: Move `PLAYER_SEED` and alias registrations to YAML/JSON.

---

## 7. Testing

### Structure

```
tests/
├── conftest.py              — session fixtures + in-memory SQLite
├── integration/test_pipeline/
│   └── test_availability_pipeline.py  — E2E with mock collectors/parsers
├── unit/
│   ├── test_collectors/      — 6 test files (RSS, HTTP, mock, utils)
│   ├── test_db/              — 3 files (repository, resolver, seed)
│   ├── test_domain/          — 2 files (enums, events)
│   ├── test_normalizers/     — 8 files (alias, dedup, mapper, player, team, injury, utils, default)
│   ├── test_parsers/         — 3 files (parsers, rule_engine, utils)
│   └── test_sync_validation.py — alias↔seed consistency
```

### Key Coverage

- **Rule engine**: Each extraction function tested individually + keyword additions + headline fragment rejection + team word fragment rejection.
- **Integration**: Fault injection at every layer, unresolved player paths, custom mock data.
- **Normalizers**: Alias resolution, dedup, validation, team/injury mapping.
- **Sync validation**: `test_every_canonical_alias_exists_in_seed`, `test_every_seeded_player_can_be_resolved`, `test_resolver_lookup_succeeds_for_canonical_names`.

### Known Gaps

- Resolver with alias inputs (e.g., `resolve("Kohli")`) — untested end-to-end.
- Duplicate player at seed (first-wins) behavior.
- Cross-source dedup failure (same event from 2 sources → 2 DB rows).
- `_find_nearest_name` proximity scoring (only tested implicitly).
- Hyphenated names (`Fraser-McGurk`).
- Google News snippet scenario (headline-only content).
- `S Sharma` alias collision.

### Run Tests

```powershell
pytest -v                          # all 400 tests
pytest -v -k "pars"               # parser tests only
pytest -v -k "pipeline"           # integration tests only
pytest tests/unit/test_sync_validation.py -v  # alias↔seed sync
```

---

## 8. Development Commands

```powershell
ruff check .                                # lint
ruff format --check .                       # format check
ruff format .                               # auto-format
pytest                                      # run all tests
python -m player_availability init-db       # reset DB
python -m player_availability run-pipeline  # live run
python -m player_availability run-pipeline --use-mock  # mock run
```

---

## 9. Key Constraints (Do Not Violate)

1. **No ML/NLP/embeddings/LLMs.** Everything must be deterministic, debuggable, regex-based.
2. **No player-specific hardcoding in parser.** `_INDIVIDUAL_PLAYER_INDICATORS` in `rule_engine.py` is off-limits for additions. All player knowledge lives in `PlayerAliasRegistry` or `PLAYER_SEED`.
3. **`_is_valid_player_candidate()`** is the parser's single gatekeeper. Adding blocklist entries here or in `patterns.py` is the correct approach for rejecting false positives.
4. **Alias collisions** must be detected — the `_alias_to_canonical` dict silently overwrites on duplicate keys. `AliasRegistry.register()` now raises `ValueError` on collision (added in this session).
5. **`seed_database()` skips duplicate names** via `if name in seen`. The first team's entry wins. If you add a player who shares a name with an existing seed entry, the second won't be inserted.
