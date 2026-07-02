# IPL Player Availability Intelligence Pipeline — Architecture Review

> Reviewed by: Senior Engineer onboarding session  
> Date: 2026-07-02  
> Codebase: `player-availability` (Component 7 of IPL Championship Prediction System)

## Changelog (Latest Update: 2026-07-02)

### Changes Applied This Session

The following items from the original review have been addressed:

1. **Parser contamination eliminated** (Sections 3.1/3.2): Added 20+ headline fragments (`HEADLINE_FRAGMENTS`) and 3 generic nouns (`GENERIC_NOUNS`) to `patterns.py`. Extended `_is_team_name_exact()` with `_TEAM_WORD_FRAGMENTS` set (module-level, built from all team variants). Result: 15 fewer contaminated records reaching the normalizer.

2. **Seed spelling fix** (Section 3.5): Corrected "Kuldeep Yadav" → "Kuldip Yadav" for CSK entry. The pre-existing CSK entry was actually a different player but shared a name string with KKR's Kuldeep Yadav. Also noted: the duplicate-name skip (`if name in seen`) meant KKR's Kuldeep Yadav was silently dropped when the CSK version was inserted first. Now both have distinct names.

3. **Alias registry expanded** (Section 3.6): Added 6 new aliases: Quinton → Quinton de Kock, Hasaranga → Wanindu Hasaranga, Emanjot → Emanjot Chahal, Esterhuizen → Connor Esterhuizen, Bethell → Jacob Bethell, Ruchir Ahir → Ruchit Ahir (typo alias). All verified as uniquely resolvable.

4. **Sync validation test added**: `test_sync_validation.py` verifies every canonical alias exists in seed, every seeded player can be resolved, and resolver lookup succeeds for all canonical names.

5. **`signs?` verb regex**: Changed `(?:signs|names|...)` to `(?:signs?|names|...)` to match bare "sign" (e.g., "SK sign Akash Madhwal").

6. **Test suite expanded**: +39 tests (32 parser + 7 normalizer). Total now **400 tests** (up from ~300 when this review was written).

### Remaining Items (Unchanged)

- **S Sharma alias collision** (Sandeep Sharma vs Suyash Sharma) — still unresolved.
- **Duplicate seed players across teams** (15 players in 2+ teams) — partially noted but not fixed.
- **Exact-match-only resolver** — no fuzzy matching added.
- **Cross-run dedup** — no DB-level unique constraint added.
- **Hyphenated name regex** — `_PLAYER_RE` still doesn't match Fraser-McGurk, Naveen-ul-Haq.
- **All-caps title handling** — `name.isupper()` check still rejects uppercase article titles.
- **Dead `pass` branch** at rule_engine.py:445-446 — still a pass.
- **MockParser unconditionally added** to live pipeline.

---

## 1. Architecture in Plain English

The system is a **deterministic, multi-stage ETL pipeline** that monitors live cricket news sources for player availability signals and persists structured events to SQLite.

### Execution Flow

```
python -m player_availability run-pipeline
        │
        ▼
__main__.py  ─── wires up collectors, parsers, normalizers, repo, resolver
        │
        ▼
AvailabilityPipeline.run()
        │
   ┌────┴────────────────────────────────────────────────────────────┐
   │ 1. COLLECT                                                       │
   │    GenericRSSCollector(source_name, url)                         │
   │      → fetch_with_retry() [httpx, exponential backoff]          │
   │      → parse_rss_items()  [stdlib xml.etree, namespace-stripped] │
   │      → list[RawData]                                             │
   └────┬────────────────────────────────────────────────────────────┘
        │
   ┌────┴────────────────────────────────────────────────────────────┐
   │ 2. PARSE                                                         │
   │    GenericArticleParser / ESPNCricinfoParser / IPLOfficialParser │
   │      → parser.can_handle(raw.source_name)                        │
   │      → parse_article(raw_data, source_name)  [rule_engine.py]   │
   │        ├── clean_html()  [BeautifulSoup + lxml]                  │
   │        ├── _find_all_keyword_matches()  [keyword scan, O(n·k)]   │
   │        ├── _find_nearest_name()  [regex + proximity scoring]     │
   │        ├── extract_team_name(), extract_injury_type()            │
   │        ├── extract_replacement() / _extract_replacement_pair()   │
   │        ├── extract_effective_date(), determine_confidence()       │
   │        └── _deduplicate_records()                                 │
   │      → list[ParsedRecord]                                         │
   └────┬────────────────────────────────────────────────────────────┘
        │
   ┌────┴────────────────────────────────────────────────────────────┐
   │ 3. NORMALIZE                                                      │
   │    DefaultNormalizer                                              │
   │      → PlayerNameNormalizer  [AliasRegistry exact match]         │
   │      → TeamNameNormalizer    [AliasRegistry exact match]         │
   │      → InjuryNormalizer      [variant → canonical]               │
   │      → validate_record()     [publisher/noun/country filter]      │
   │      → Deduplicator          [key = player+event+source+date]    │
   │      → list[NormalizedRecord]                                     │
   └────┬────────────────────────────────────────────────────────────┘
        │
   ┌────┴────────────────────────────────────────────────────────────┐
   │ 4. MAP + STORE                                                    │
   │    normalized_to_event_create(record, player_resolver)           │
   │      → DbPlayerResolver.resolve(player_name, team_name)          │
   │          └── SELECT * FROM players WHERE name = canonical        │
   │              (exact match only, optional team join)               │
   │      → EventCreate (Pydantic domain model)                        │
   │    SqlRepository.add_event()                                      │
   │      → INSERT INTO availability_events                            │
   └─────────────────────────────────────────────────────────────────┘
```

### Key Data Structures

| Stage | Structure | Type |
|---|---|---|
| After collect | `RawData` | `@dataclass` |
| After parse | `ParsedRecord` | `@dataclass` |
| After normalize | `NormalizedRecord` | `@dataclass` |
| Domain event | `EventCreate` / `AvailabilityEvent` | `pydantic.BaseModel` |
| ORM | `PlayerModel`, `TeamModel`, `AvailabilityEventModel` | SQLAlchemy `DeclarativeBase` |

---

## 2. Architecture Strengths

### 2.1 Clean Layer Separation
Every layer has a single responsibility. `RawData` → `ParsedRecord` → `NormalizedRecord` → `EventCreate` is a clearly typed one-way transformation chain. No layer reaches back up.

### 2.2 Abstract Base Classes Everywhere
`BaseCollector`, `BaseParser`, `BaseNormalizer`, `AbstractRepository`, `PlayerResolver` — all are properly abstracted. New sources can be added by subclassing without touching the pipeline.

### 2.3 Deterministic Extraction
The rule engine uses keyword scanning and regex — fully deterministic, reproducible, no external ML API calls. This is the correct approach for a production pipeline that must be debuggable.

### 2.4 AliasRegistry Design
The `AliasRegistry` / `PlayerAliasRegistry` / `TeamAliasRegistry` pattern is clean. A single O(1) dict lookup maps any alias or abbreviation to its canonical form. Extensible via `register()` without touching core logic. Now includes collision detection (`register()` raises `ValueError` on duplicate alias).

### 2.5 Resilience Built In
- `fetch_with_retry` with exponential backoff handles transient HTTP failures.
- The pipeline catches `CollectError`, `ParseError`, `NormalizeError`, `UnresolvedPlayerError` per item — one source failing does not abort the run.
- Collector-level, parser-level, and normalizer-level fault isolation is tested.

### 2.6 Priority-Ordered Event Detection
`EVENT_PRIORITY` ensures that `RULED_OUT` beats `INJURY` for the same article — the most actionable signal wins. Per-article deduplication prevents emitting duplicate records for the same player from the same article.

### 2.7 Session Management
`get_session()` as a context manager with commit/rollback is correct. `expire_on_commit=False` prevents N+1 lazy-load crashes after commit.

### 2.8 Test Coverage Breadth
~400 tests span unit (rule engine functions, all normalizers, repository) and integration (full pipeline with in-memory SQLite). Fault injection tests cover every layer. A sync validation test now ensures alias↔seed consistency.

---

## 3. Weaknesses and Bottlenecks

This is where the production gap lives. The stated problem — 150 articles collected, ~100 normalized, **very few stored** — is explained entirely by the items below.

### 3.1 Player Resolution: Exact-Match-Only (Critical Bottleneck)

**Location:** [`db/resolver.py:24`](file:///c:/Users/Jash%20Ajmera/OneDrive/Desktop/College/Coding/clubs/sqac/IPL-predictor/player-availability/src/player_availability/db/resolver.py#L24)

```python
stmt = select(PlayerModel).where(PlayerModel.name == canonical)
```

This is a **strict equality check** against the canonical name stored in the database. For a player to be stored, all of the following must succeed in sequence:

1. The rule engine must extract a player name string from the article.
2. `PlayerNameNormalizer` must map that string to a canonical via `AliasRegistry`.
3. The canonical must **exactly** match a `PlayerModel.name` in the database.

This breaks for any player name that:
- Uses a slightly different spelling (e.g., `"Mohd Siraj"` vs `"Mohammed Siraj"`)
- Is not yet in `PlayerAliasRegistry` (new signings, replacements, uncapped players)
- Is extracted correctly by the rule engine but is not a top-50 player (e.g., "Mukesh Kumar" resolved correctly but DB entry uses different spelling)
- Is in the DB under a team that doesn't match what the article mentions

Every unresolved player produces a logged error and **no stored event**. This is the primary reason stored counts are low.

### 3.2 Player Name Extraction: Regex is Brittle (Extraction Bottleneck)

**Location:** [`parsers/rule_engine.py:23`](file:///c:/Users/Jash%20Ajmera/OneDrive/Desktop/College/Coding/clubs/sqac/IPL-predictor/player-availability/src/player_availability/db/resolver.py)

```python
_PLAYER_RE = re.compile(r"(?:[A-Z]{1,2}\.?\s+)?[A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2}")
```

This regex will **miss**:
- Fully capitalised names in headlines (e.g., `"JASPRIT BUMRAH RULED OUT"`) — `_is_valid_player_candidate` rejects `name.isupper()`.
- Names with initials in different formats: `"T. Natarajan"`, `"Mohammad Nabi"` (both `[A-Z][a-z]+`, but "Mohammad" is fine — however `T. Natarajan` triggers a different regex group).
- Three-part names where the second word is lowercase (e.g., `"Faf du Plessis"` — `du` is lowercase, which breaks `{0,2}` continuation).
- Hyphenated names: `"Jake Fraser-McGurk"`, `"Naveen-ul-Haq"`.

**Current workaround:** `_INDIVIDUAL_PLAYER_INDICATORS` — a hardcoded regex of ~80 known surnames used in proximity scoring. This is functional but fragile.

### 3.3 Routing Mismatch: Live RSS Sources vs Registered Parsers

**Location:** [`__main__.py:103-106`](file:///c:/Users/Jash%20Ajmera/OneDrive/Desktop/College/Coding/clubs/sqac/IPL-predictor/player-availability/src/player_availability/__main__.py#L103)

```python
parsers = [MockParser()]
for source in settings.source_registry:
    if source.is_active:
        parsers.append(GenericArticleParser(source_name=source.name))
```

The two active live sources are `rediff_cricket` and `google_cricket_news`. When articles arrive with `source_name="rediff_cricket"`, the pipeline looks for a parser where `parser.can_handle("rediff_cricket")` is `True`. `MockParser` handles `"mock"`, not `"rediff_cricket"`. `GenericArticleParser` is instantiated with `source_name=source.name` — so this should work. But: `MockParser` is always added first, and `ESPNCricinfoParser`/`IPLOfficialParser` are **not** added in the live path. These parsers would never see live RSS data even if called. This is a minor code smell, not a bug.

### 3.4 Deduplication Key Doesn't Cross Sources (Silent Data Loss)

**Location:** [`normalizers/deduplication.py:10-14`](file:///c:/Users/Jash%20Ajmera/OneDrive/Desktop/College/Coding/clubs/sqac/IPL-predictor/player-availability/src/player_availability/normalizers/deduplication.py#L10)

```python
@dataclass(frozen=True)
class DedupKey:
    player_name: str
    event_type: EventType
    source_name: str       # <-- includes source
    effective_date: date | None
```

`source_name` is part of the dedup key. This means **the same event can be stored multiple times if it appears in multiple sources** (e.g., Bumrah's injury is covered by both rediff and google_news → two identical `availability_events` rows). This defeats the purpose of deduplication.

### 3.5 Seed Data Has Duplicate Players Across Teams

**Location:** [`db/seed.py`](file:///c:/Users/Jash%20Ajmera/OneDrive/Desktop/College/Coding/clubs/sqac/IPL-predictor/player-availability/src/player_availability/db/seed.py)

The following players appear in two different teams in `PLAYER_SEED`:

| Player | Teams |
|---|---|
| Pat Cummins | KKR and SRH |
| David Warner | SRH and DC |
| Ajinkya Rahane | CSK and DC |
| Shreyas Iyer | KKR and DC |
| Ravichandran Ashwin | RR and DC |
| Harshal Patel | RCB and PBKS |
| Rishabh Pant | DC and PBKS |
| Shikhar Dhawan | DC and PBKS |
| Hardik Pandya | MI and GT |
| Ravindra Jadeja | CSK and GT |
| Shimron Hetmyer | RR and DC |
| Marcus Stoinis | DC and LSG |
| Avesh Khan | RR and LSG |
| Mujeeb Ur Rahman | KKR and RR |
| Kagiso Rabada | DC and PBKS |

But `seed_database()` guards against double-insertion with `if name in seen: continue` at line 292 — **the first occurrence wins**. So Pat Cummins is inserted as a KKR player, never as SRH. This means `DbPlayerResolver.resolve("Pat Cummins", "Sunrisers Hyderabad")` will find 0 rows and fail. These are likely stale/outdated squad entries from a previous IPL season.

**Note:** This session fixed one instance of the same bug at a different level: "Kuldeep Yadav" was incorrectly listed for CSK (should be "Kuldip Yadav", a different player). The name collision meant KKR's Kuldeep Yadav was silently skipped during seeding. This is now fixed with distinct names.

### 3.6 `Sandeep Sharma` and Other Ambiguous Aliases

In `PlayerAliasRegistry` (player.py line 154):
```python
self.register("Sandeep Sharma", "S Sharma")
```

But line 130 also registers:
```python
self.register("Suyash Sharma", "S Sharma")
```

`"S Sharma"` is registered **twice** to different canonicals. The second `register()` call will **silently overwrite** the first in the dict. This is a data integrity bug.

### 3.7 Google News RSS: Article Content is Just Headlines

Google News RSS `<description>` elements typically contain only a 1–2 sentence snippet or just the article title, not full article body. The pipeline sets `fetch_full_article=False` by default, so **the body text passed to the rule engine is extremely sparse**. Player name extraction degrades significantly when context is absent.

### 3.8 `_find_nearest_name` Scoring Logic Has a Dead Branch

**Location:** [`parsers/rule_engine.py:445-446`](file:///c:/Users/Jash%20Ajmera/OneDrive/Desktop/College/Coding\clubs\sqac\IPL-predictor\player-availability\src\player_availability\parsers\rule_engine.py#L445)

```python
if any(word[0].isupper() and len(word) > 1 and word[0].isupper() for word in name.split()):
    pass  # <-- this branch does nothing
```

The condition is always true for any valid capitalized name (since `_is_obviously_not_player` already filtered bad names). The `pass` was presumably a placeholder for a score bonus that was never implemented.

### 3.9 Confidence Ordering Bug

**Location:** [`parsers/rule_engine.py:489-506`](file:///c:/Users/Jash%20Ajmera/OneDrive/Desktop/College/Coding/clubs/sqac/IPL-predictor/player-availability/src/player_availability/parsers/rule_engine.py#L489)

```python
for phrase in HIGH_CONFIDENCE_PHRASES:
    if phrase in text_lower:
        return ConfidenceLevel.HIGH

for phrase in LOW_CONFIDENCE_PHRASES:
    if phrase in text_lower:
        return ConfidenceLevel.LOW
```

`HIGH_CONFIDENCE_PHRASES` includes `"ruled out"`. `LOW_CONFIDENCE_PHRASES` includes `"may miss"`, `"could be"`, etc. But the order of checking is HIGH → LOW → MEDIUM, and the function returns **immediately** on the first match. A phrase like `"speculation that he is ruled out"` returns `HIGH` — which the tests actually document as correct behaviour. This is a minor ordering issue to be aware of, but works as designed.

### 3.10 `validate_record` Conflation

**Location:** [`normalizers/utils.py:106-107`](file:///c:/Users/Jash%20Ajmera/OneDrive/Desktop/College/Coding/clubs/sqac/IPL-predictor/player-availability/src/player_availability/normalizers/utils.py#L106)

```python
if errors and record.confidence == ConfidenceLevel.LOW:
    errors.append("confidence is LOW, combined with other issues")
```

This code adds to `errors` only when there are *already* other errors. But since `if errors:` at line 116 raises `ValidationError` regardless, this extra append is only cosmetic — it adds one more sentence to the error message. Not a functional bug, but a logic smell.

### 3.11 No Cross-Run Deduplication at the DB Level

There is no unique constraint on `availability_events` (e.g., on `player_id + event_type + event_date + source_name`). Every pipeline run can insert **duplicate rows** for the same event if it appears in the RSS feed across multiple runs. The deduplicator only operates within a single pipeline run's in-memory batch.

---

## 4. Technical Debt

| Item | Location | Severity | Status |
|---|---|---|---|
| Duplicate player entries in `PLAYER_SEED` across teams | `db/seed.py` | High | Open |
| `S Sharma` alias assigned to two different players | `normalizers/player.py:130,154` | High | Open |
| Dead `pass` branch in `_find_nearest_name` | `parsers/rule_engine.py:445-446` | Low | Open |
| `MockParser` unconditionally added to live pipeline | `__main__.py:103` | Low | Open |
| No DB-level unique constraint on events | `db/models.py` | Medium | Open |
| Google News snippet content (no full article fetching) | `config.py` + `generic_rss.py` | Medium | Open |
| `_INDIVIDUAL_PLAYER_INDICATORS` is a maintenance burden | `parsers/rule_engine.py:454` | Medium | Open |
| `ESPNCricinfoParser` / `IPLOfficialParser` are never wired to live sources | `__main__.py` | Low | Open |
| No logging of how many players were unresolved vs. why | `pipeline/availability_pipeline.py` | Low | Open |
| `validate_record` `LOW confidence + other errors` is dead logic | `normalizers/utils.py:106` | Low | Open |
| Seed spelling "Kuldeep Yadav" → "Kuldip Yadav" (CSK) | `db/seed.py` | Medium | **Fixed** |
| Parser contamination: headline/team/noun leakage | `parsers/patterns.py`, `rule_engine.py` | High | **Fixed** |
| Missing player aliases (Quinton, Hasaranga, etc.) | `normalizers/player.py` | Medium | **Fixed** |
| Alias↔seed sync validation test | `tests/unit/test_sync_validation.py` | Low | **Added** |
| `signs?` verb regex (bare "sign" not matched) | `parsers/rule_engine.py` | Low | **Fixed** |

---

## 5. Code Quality Review

### Positive
- Consistent use of `@dataclass` for internal transfer objects; Pydantic only for domain/API boundary models. This is idiomatic.
- Type annotations throughout. Python 3.12 union syntax (`X | Y`) used consistently.
- `loguru` used uniformly for structured logging with `{}` interpolation placeholders.
- `StrEnum` / `IntEnum` for domain enums — `.value` is a string/int, safe to store directly.
- `AliasRegistry.resolve()` is O(1) dict lookup.
- HTTP client creates a fresh `httpx.Client` per request — avoids connection pool state leakage but is slightly inefficient (see Performance section).

### Areas for Improvement
- `rule_engine.py` is a 716-line file with 15+ module-level functions. It does a lot. Consider splitting into `extraction.py` (name/team/injury/date/replacement extraction) and `classification.py` (event type detection, confidence, status mapping). Not required now — the existing structure is readable — but worth noting for when it grows.
- `_INDIVIDUAL_PLAYER_INDICATORS` (a hardcoded regex of ~80 surnames) will need to be maintained manually forever. This is acceptable for now given the constraint of no ML/NLP, but should be documented as such.
- `normalizers/utils.py` imports from `player_availability.domain.enums` and `player_availability.parsers.patterns` using absolute paths (not relative). All other normalizer files use relative imports. Minor inconsistency.
- `seed.py` uses `session.query()` (legacy ORM style) while `repository.py` uses `select()` (new 2.0 style). Should be unified.

---

## 6. Testing Review

### Strengths
- **Rule engine tests** (`test_rule_engine.py`, ~390 lines) are comprehensive: each extraction function is tested individually, plus `TestNewKeywords` validates ~20 keyword additions, plus 32 new tests for team fragments, headline fragments, month names, sign verb, Dhoni Still, He Last Played.
- **Integration tests** (`test_availability_pipeline.py`, 329 lines) cover end-to-end with in-memory SQLite: fault injection at every layer, unresolved players, custom mock data.
- **Normalizer tests** cover alias resolution, deduplication, validation, and team/injury normalization separately.
- **Sync validation tests** (`test_sync_validation.py`) verify alias↔seed consistency — ensures every canonical alias exists in seed and every seeded player can be resolved.
- In-memory SQLite fixture in `conftest.py` is correct — no shared global state between tests.

### Gaps
- **No test for the `DbPlayerResolver` with alias inputs**: e.g., `resolve("Kohli")` — does it normalize the name first and find "Virat Kohli"? (It does, via `PlayerNameNormalizer.normalize()` — but this is untested.)
- **No test for the `seed.py` duplicate player problem** — specifically that the first occurrence wins and the second is silently skipped.
- **No test for cross-source deduplication failure** — two normalized records for the same event but different `source_name` will produce two DB rows.
- **No test for `_find_nearest_name` context scoring** — proximity-to-keyword scoring is the heart of player extraction but is only tested implicitly.
- **No test for hyphenated player names** (`Jake Fraser-McGurk`, `Naveen-ul-Haq`) in the rule engine regex.
- **No regression test for the `S Sharma` alias collision**.
- **No test for the Google News snippet scenario** — where `content` is just a headline and `title` is the only useful signal.

---

## 7. Performance Review

- **Sequential HTTP fetching**: Each collector makes synchronous HTTP calls. With multiple sources and retries (up to `max_retries=3`, `timeout=30s`), a pipeline run can take several minutes if sources are slow. No `asyncio`, no parallelism. Acceptable for current scale (2 sources, ~150 articles), but will need addressing if sources scale.
- **New `httpx.Client` per request**: A fresh connection pool is created and destroyed for each fetch. A singleton client with connection pooling would be faster.
- **`xml.etree.ElementTree.fromstring` without streaming**: Fine for RSS feeds (typically < 1MB). Not a concern.
- **O(n·k) keyword scan per article**: For each article, `_find_all_keyword_matches` iterates over 10 event types × average 10 keywords = ~100 string searches per article. For 150 articles this is ~15,000 `str.find()` calls. Negligible.
- **Full-article fetching disabled by default**: `fetch_full_article=False`. Enabling it would significantly improve extraction quality for Google News but adds latency proportional to article count.

---

## 8. Maintainability Review

- **Adding a new source**: Subclass `BaseCollector` (or just use `GenericRSSCollector` directly), add a `SourceEntry` to `config.py`, add a `GenericArticleParser(source_name=...)` — done. Well-structured.
- **Adding a new player**: Add a `register()` call in `PlayerAliasRegistry._register_known_players()` + a row in `PLAYER_SEED`. Currently requires code change + re-seeding. Could become a CSV/JSON external config.
- **Adding a new event type**: Add to `EventType` enum, `EVENT_KEYWORDS`, `EVENT_PRIORITY`, `map_event_to_status()`, update keyword tests. Well-isolated.
- **Risk of alias registry divergence**: The alias registry in `normalizers/player.py` and the DB seed in `db/seed.py` must be kept in sync. If a canonical name in the registry doesn't match any `PlayerModel.name` exactly, resolution will always fail for that player. **A sync validation test now checks this.**

---

## 9. Scalability Review

- SQLite is appropriate for current scale (10 teams × ~25 players = 250 players, likely < 10,000 events per season).
- No indexes defined on `availability_events` beyond the default primary key. For `player_id + is_active` queries (used in `get_current_status`), a composite index would help once rows reach thousands.
- Pipeline is single-process, single-threaded. Adequate for a daily or hourly batch job.
- The architecture is clean enough that swapping SQLite for PostgreSQL requires only `database_url` config change and `create_engine` — no ORM changes needed.

---

## 10. Root Cause of the Core Problem

> **~150 articles collected → ~100 normalized → very few stored**

The gap from 100 normalized to few stored is almost entirely `UnresolvedPlayerError`. Tracing the chain:

1. A player name is extracted from an article (e.g., `"Shami"`, `"Mohammad Siraj"`, `"AB de Villiers"`).
2. `PlayerNameNormalizer.normalize("Shami")` → resolves to `"Mohammed Shami"` ✓
3. `DbPlayerResolver.resolve("Mohammed Shami")` → `SELECT * FROM players WHERE name = 'Mohammed Shami'` → finds row ✓
4. But for `"Mohammad Siraj"` (one 'd' less): → normalizes to `"Mohammed Siraj"` ✓ → DB has `"Mohammed Siraj"` ✓ — works.
5. But for `"Siraj"` → alias registry maps to `"Mohammed Siraj"` ✓ → DB query succeeds ✓.
6. **Fails for**: any player not in `PlayerAliasRegistry`, any player name extracted in a form the registry doesn't know, or any player whose DB entry name doesn't match the canonical the registry produces.

The **secondary cause** is extraction failures: articles where the player name is all-caps, hyphenated, or appears in a context that `_find_nearest_name` scores poorly. These produce `parsed_count=0` entries that never reach the normalizer.

---

## 11. Prioritized Implementation Roadmap

### Priority 1 — Fix Data Integrity Bugs (Before Any Pipeline Run)

These are silent correctness bugs that will corrupt the database.

1. **Fix `S Sharma` alias collision** in `PlayerAliasRegistry`: `Sandeep Sharma` and `Suyash Sharma` both claim `"S Sharma"`. The second registration silently overwrites the first. Add a collision guard to `AliasRegistry.register()` (raise or log a warning), then deduplicate these aliases.

2. **Audit and fix `PLAYER_SEED` duplicate players across teams**: Fifteen players appear in 2 teams. Most reflect historical squad data. Decide the authoritative team per player (current 2026 squad) and remove duplicates. Add a DB-level `UNIQUE` constraint on `(name, team_id)` or at minimum on `(name)` with a migration note.

3. **Add a DB-level unique constraint on `availability_events`**: Suggest `(player_id, event_type, source_name, event_date)`. This prevents duplicate rows being inserted on repeated pipeline runs.

### Priority 2 — Improve Player Resolution (Core Bottleneck)

4. **Fuzzy name matching fallback in `DbPlayerResolver`**: When exact match fails, attempt a case-insensitive `LIKE '%surname%'` query scoped to the team (if known). Return the match if exactly one candidate is found. This alone will recover a large fraction of unresolved events.

5. **Add consistency check between `PlayerAliasRegistry` and `PLAYER_SEED`**: Write a utility (or a test) that verifies every canonical name in `PlayerAliasRegistry` appears in `PLAYER_SEED` (or vice versa). Run this check as part of CI. **✅ Done — `test_sync_validation.py` covers this.**

6. **Expand `PlayerAliasRegistry`** to cover the ~30 players in `PLAYER_SEED` that currently have no alias entries (e.g., `Suryansh Shedge`, `Harvik Desai`, `Maxwell Bryant`, `Shams Mulani`, etc.).

### Priority 3 — Improve Extraction Quality (Extraction Bottleneck)

7. **Fix regex for hyphenated names** in `_PLAYER_RE`: update pattern to `(?:[A-Z]{1,2}\.?\s+)?[A-Z][a-z]+(?:[-\s][A-Za-z][a-z]+){0,3}` to allow `Fraser-McGurk`, `Naveen-ul-Haq`.

8. **Handle all-caps article titles**: When `_PLAYER_RE` finds no candidates (because `name.isupper()` rejects them), try `title.title()` to convert the title to title-case and re-run extraction.

9. **Title-priority extraction for low-content articles**: If article body is < 100 characters (Google News snippet only), skip body parsing and rely entirely on `extract_player_name_from_title`. This avoids spurious name matches from ultra-short descriptions.

10. **Remove the dead `pass` branch** in `_find_nearest_name` at line 445–446 and implement the intended scoring bonus (e.g., `score -= 20.0` for names containing known surnames from `_INDIVIDUAL_PLAYER_INDICATORS`).

### Priority 4 — Cross-Run Deduplication

11. **Pre-insert duplicate check in `SqlRepository.add_event()`**: Before inserting, query for an existing event with the same `(player_id, event_type, event_date, source_name)`. If found, skip insert (or update if confidence is higher).

### Priority 5 — Observability and Maintenance

12. **Log the reason for each unresolved player** at DEBUG level (not just the fact that it failed). Log the extracted name, the normalized canonical, and whether the DB lookup returned 0 or >1 rows. This makes debugging extraction failures much faster.

13. **Externalise player data**: Move `PLAYER_SEED` and alias registrations to a JSON/YAML file loaded at startup. Eliminates code churn when squads change.

14. **Remove `MockParser` from live pipeline** in `__main__.py:103` — it's a no-op in production (no article has `source_name="mock"`) but adds confusion.

### Priority 6 — Infrastructure (Non-urgent)

15. **Add indexes** on `availability_events(player_id, is_active)` and `availability_events(event_date)`.

16. **Enable `fetch_full_article=True`** for `google_cricket_news` (or add a flag) to significantly improve content richness for that source.

17. **Connection pooling**: Create a shared `httpx.Client` instance on the collector rather than per-call.

---

## 12. Summary Assessment

| Dimension | Rating | Notes |
|---|---|---|
| Architecture | ✅ Strong | Clean ETL, good abstractions, proper separation |
| Data Flow | ✅ Good | Typed transformations, clear handoffs |
| Code Quality | ✅ Good | Minor inconsistencies, one dead branch |
| Testing | ✅ Good | Broad coverage (~400 tests); some resolution/extraction gaps remain |
| Performance | ⚠️ Adequate | Sequential HTTP, no pooling — fine for current scale |
| Maintainability | ⚠️ Medium | Alias registry ↔ DB sync is manual, player data in code |
| Scalability | ✅ Adequate | SQLite + single-process is fine for IPL-scale data |
| **Production Readiness** | ❌ **Blocked** | Data bugs in seed + alias collision + no cross-run dedup |

The pipeline is architecturally correct. The production gap is not a design problem — it is a **data completeness problem** (resolution scope) and **two silent data correctness bugs** (alias collision, duplicate seed entries). Fixing Priority 1 and 2 should produce a measurable improvement in stored event counts without touching the architecture.
