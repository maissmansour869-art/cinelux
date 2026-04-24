# Cinélux Cinema Booking System — Implementation-Ready PRD

**Version:** 1.0 · **Date:** April 2026 · **Status:** Final — Ready for Implementation
**Audience:** Implementation agent (an AI coding agent, or a junior dev with senior supervision)
**Scope:** 20 Functional Requirements (FR-01 … FR-20), 8 NFRs, full data model, full API, all UC flows

---

## 0. How to Use This Document

This PRD is written so an implementation agent can build the system **section-by-section without needing to ask follow-up questions**. It is organized as follows:

1. **§1 Product Overview** — what we are building and why.
2. **§2 Architectural Constraints & Decisions** — the non-negotiables (PostgreSQL, Django, single VM, monolith). Read this first; every design choice downstream follows from it.
3. **§3 System Architecture** — the layers and how a request flows through them.
4. **§4 Canonical Data Model** — the PostgreSQL schema. **This is the single source of truth.** Any ambiguity in the uploaded ERD is resolved here.
5. **§5 Authentication, Authorisation, Sessions** — applies to every endpoint.
6. **§6 Functional Requirements (FR-01 … FR-20)** — the core of the document. Each FR has:
   - Use case it serves
   - API contract (method, path, request, response, errors)
   - Flow-of-control (step-by-step)
   - Business rules
   - Data touched (tables written/read)
   - Design decisions and rationale
   - Test cases (TC-XX) mapped to the RTM
7. **§7 Non-Functional Requirements** — performance, security, reliability.
8. **§8 External Integrations** — Payment Gateway (simulated), Notification Service.
9. **§9 Error Model** — unified error schema and catalogue.
10. **§10 Project Structure & Implementation Plan** — where to put files, in what order to build.
11. **§11 Acceptance Criteria** — done-done definition.
12. **§12 Open Questions Resolved** — prior ambiguities with decisions recorded.

**Conventions:**
- `FR-XX` = Functional Requirement ID (canonical from SRS, FR-01 … FR-20).
- `UC-XX` = Use Case ID (from the use case diagram).
- `TC-XX` = Test Case ID (from the RTM).
- Code identifiers in `monospace`.
- **Bold** = must-do. *Italic* = rationale or note.
- All timestamps are ISO 8601 UTC (`2026-04-20T19:30:00Z`).
- All IDs are **UUIDv4 strings** (see §12.1 for the decision).
- All monetary amounts are stored as `NUMERIC(10,2)` and transmitted as numbers in JSON.
- All currency is **USD** unless explicitly noted per-showtime.

---

## 1. Product Overview

### 1.1 One-line description

Cinélux is a web-based cinema booking system that lets registered customers browse films and showtimes, reserve seats interactively, pay through a (simulated) payment gateway, receive a QR-coded e-ticket, manage or cancel bookings, and receive content-based movie recommendations. Cinema staff validate tickets at entry; administrators manage the catalogue and user accounts.

### 1.2 Primary actors

| Actor | Role | FRs owned |
|---|---|---|
| **Customer** (End User) | Browses catalogue, books, cancels, manages profile, receives recommendations | FR-01 … FR-14 |
| **Gate Staff** | Scans and validates QR codes at cinema entry | FR-15, FR-16 |
| **Administrator** | Manages movies, showtimes, halls, user accounts, roles | FR-17 … FR-20 |
| **Payment Gateway** (external, simulated) | Processes payments, issues refunds | called by FR-07, FR-11 |
| **Notification Service** (external) | Sends Email/SMS for confirmations and cancellations | called by FR-08, FR-11 |
| **AI Recommendation Engine** (internal component) | Content-Based Filtering over user preferences + booking history | FR-04, FR-05 |

### 1.3 Core user flows (happy path)

1. **Browse → Book:** Customer browses the catalogue → filters by genre/date → views movie details → picks showtime → selects seats → pays → receives QR e-ticket.
2. **Manage bookings:** Customer views booking history → views upcoming booking → optionally cancels within the policy window.
3. **Validate:** Gate staff scans QR → system marks the ticket USED and logs entry.
4. **Admin:** Admin adds a movie + showtime → creates/suspends user accounts → assigns roles.

---

## 2. Architectural Constraints & Decisions

These are **hard constraints**. The implementation agent must not deviate without a written escalation.

### 2.1 Non-negotiable constraints (from `Cinelux_System_Constraints.pdf`)

| ID | Constraint | Implication |
|---|---|---|
| CINELUX-CONST-01 | Three part-time student developers, ~15–20 hrs/week each | Favour simplicity; avoid exotic tooling |
| CINELUX-CONST-02 | 8–10 week fixed delivery | No mid-project re-architecture; MVP scope is locked to the 20 FRs |
| CINELUX-CONST-03 | Single Linux VM | No distributed deployment, no multi-host |
| CINELUX-CONST-04 | **PostgreSQL is the sole data store** | No Mongo, no Redis, no Elasticsearch |
| CINELUX-CONST-05 | Monolith — no microservices | One Django project, one deployable |
| CINELUX-CONST-06 | No Docker / Kubernetes | Deploy via systemd + gunicorn + nginx |
| CINELUX-CONST-07 | No Redis / caching layer | All reads hit PostgreSQL; use materialized views where needed |
| CINELUX-CONST-08 | Synchronous only — no message queues | Background jobs via APScheduler, in-process |
| CINELUX-CONST-09 | Exactly two roles: `USER` and `ADMIN` | Gate staff is modelled as a sub-role flag on ADMIN; see §5.3 |
| CINELUX-CONST-10 | Form-based UI, no WebSockets, no offline | Polling is acceptable; optimistic UI for seat selection |
| CINELUX-CONST-11 | External services are black boxes with fallbacks | Every outbound call must have a defensive fallback |
| CINELUX-CONST-12 | No raw card data stored; Admin cannot see payment credentials | Payment Gateway holds all PCI scope |

### 2.2 Technology stack (from Task 3 — Tech Stack & Rationale)

| Layer | Choice | Why |
|---|---|---|
| Frontend | **React 18** (SPA, Vite) | Two team members have React experience; component model fits the booking flow |
| Backend | **Python 3.11 + Django 5.x + Django REST Framework** | Python is the team's strongest backend language; DRF gives clean REST APIs quickly; Django Admin solves FR-17 … FR-20 for free in worst case |
| Database | **PostgreSQL 15+** | ACID, row-level locking (critical for seat reservation), JSONB for flexible movie metadata, native array types |
| Recommendations | **scikit-learn + pandas** (Content-Based Filtering) | CPU-only, no GPU required; fits single-VM constraint |
| Background jobs | **APScheduler** (in-process) | No broker needed; handles notification retries and booking-expiry sweeps |
| Auth | **JWT bearer tokens** via `djangorestframework-simplejwt`; passwords hashed with **BCrypt** (or Django's default `PBKDF2` — see §12.2) | NFR-02 |
| Version control | Git + GitHub | Team already uses it |
| Deploy | Single Linux VM: **gunicorn** (app) + **nginx** (reverse proxy + static) + **PostgreSQL** (local) | Fits CINELUX-CONST-03 |

### 2.3 Explicitly NOT using

Node.js/Express, MongoDB, Redis, Celery, TensorFlow/PyTorch, Docker, Kubernetes. Rationales in the source tech-stack doc — do not re-litigate.

### 2.4 Architectural style

**Layered + Client-Server monolith**, six layers:

```
┌─────────────────────────────────────────────────────┐
│  Client Layer: React SPA (Customer UI + Admin UI)   │
└───────────────────────┬─────────────────────────────┘
                        │ HTTPS / JSON
┌───────────────────────▼─────────────────────────────┐
│  API Layer (DRF ViewSets & APIViews)                │
│  UserAPI  CatalogueAPI  BookingAPI  AdminAPI  RecAPI│
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│  Service Layer (pure Python — no ORM calls here)    │
│  UserService  CatalogueService  BookingService      │
│  AdminService  RecommendationService  ValidationSvc │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│  Data Access Layer (Django ORM — Repositories)      │
│  UserRepo  CatalogueRepo  BookingRepo  ...          │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│  Database Layer: PostgreSQL                         │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
          ┌──────────────────────────────┐
          │ External (synchronous HTTP)  │
          │  Payment Gateway (simulated) │
          │  Notification Service        │
          └──────────────────────────────┘
```

**Layer rules** (enforced by code review):

| Layer | Does | Does NOT |
|---|---|---|
| Client | Renders UI, sends JSON requests, displays responses | No business logic, no DB access |
| API | Parses/validates requests, routes to a Service, serializes responses | No ORM calls, no business rules |
| Service | Applies business rules, orchestrates repositories and externals | No direct DB queries (goes via Repo), no request/response objects |
| Repository (DAL) | Executes ORM queries, returns plain model instances or dicts | No business logic, no HTTP |
| Database | Stores data, enforces integrity | Application logic stays in code, not triggers (except for `updated_at`) |
| External | Payment Gateway, Notification Service — black boxes | Cinélux does not implement these |

*Why a service layer when Django views could call the ORM directly?* Because §3.2 specifies test cases that exercise services without the HTTP layer, and because booking logic (with seat locking, payment, notification) must be testable in isolation.

---

## 3. System Architecture — Request Flow

### 3.1 Standard request flow

```
React → POST /api/... + JWT
  → API: DRF view validates JSON schema with a Serializer
  → Service: business rules + orchestration inside a DB transaction
    → Repository: ORM query
      → PostgreSQL
    → External HTTP (if needed): Payment Gateway / Notification Service
  → API: serializes the Service's return value
  → React: renders
```

### 3.2 Transactions

- **Every mutating endpoint runs inside a single `django.db.transaction.atomic()` block** at the Service layer (not the View). This guarantees that if a notification fails, the DB is consistent.
- **Seat reservation uses `SELECT ... FOR UPDATE`** (via Django's `select_for_update()`) on the affected `bookings`/`seats` rows to prevent double-booking under concurrency. See §6.6 (FR-06) for the exact query.

### 3.3 External call policy

Every external call **must**:

1. Have a timeout (default **5 seconds**).
2. Have a fallback behaviour documented per call site (§8).
3. Be wrapped in a try/except that logs the failure and does not crash the parent flow.
4. Never appear in critical-path code where failure would block a user action, except where explicitly required (e.g. payment in FR-07).

### 3.4 Background jobs (APScheduler)

Three scheduled jobs run in-process:

| Job | Schedule | Purpose |
|---|---|---|
| `notification_retry_sweep` | every 5 min | retry notifications with `status = 'FAILED'` up to 3 times |
| `booking_hold_expiry` | every 1 min | release seats held > 10 minutes without confirmation (§6.6) |
| `rec_similarity_refresh` | daily at 03:00 | refresh the `mv_movie_similarity` materialized view (§6.4) |

---

## 4. Canonical Data Model (PostgreSQL)

This section is the authoritative schema. The uploaded ERD is the starting point; **this section supersedes it** where they conflict.

### 4.1 Design choices resolved

| Question | Decision |
|---|---|
| Primary key type | **UUIDv4 strings**, `CHAR(36)` or native `UUID` type. See §12.1 |
| Seat ownership | Seats belong to a **Hall**, not a Showtime. A Showtime inherits the Hall's seat map. Booking links `showtime_id + seat_id`. |
| Pricing | Stored on the **Showtime** (flat price per showtime for MVP). See §12.3. |
| Booking-seat cardinality | **One row in `bookings` per booked seat**. A multi-seat purchase creates N rows linked by `booking_group_id`. See §12.4. |
| Soft delete | **Movies** use soft delete (`is_active`). **Bookings** use status (`CANCELLED`), not delete. |
| Timestamps | Every table has `created_at` and (where mutable) `updated_at`, both `TIMESTAMPTZ DEFAULT NOW()`. |

### 4.2 Tables

Schema below uses PostgreSQL DDL. Indexes and constraints are included.

```sql
-- =====================================================================
-- USERS & AUTH
-- =====================================================================
CREATE TABLE users (
    user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,      -- BCrypt / PBKDF2
    phone           VARCHAR(30),
    role            VARCHAR(20) NOT NULL DEFAULT 'USER'
                    CHECK (role IN ('USER', 'ADMIN', 'STAFF')),
    status          VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
                    CHECK (status IN ('ACTIVE', 'SUSPENDED')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_role  ON users (role);

-- Genre lookup (small, static) -----------------------------------------
CREATE TABLE genres (
    genre_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(60) NOT NULL UNIQUE
);

-- User's preferred genres (for cold-start and CBF) ---------------------
CREATE TABLE user_genre_preferences (
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    genre_id        UUID NOT NULL REFERENCES genres(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, genre_id)
);

-- =====================================================================
-- CATALOGUE
-- =====================================================================
CREATE TABLE movies (
    movie_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    release_date    DATE,
    language        VARCHAR(40),
    age_rating      VARCHAR(10),        -- e.g. 'PG', 'PG-13', 'R'
    poster_url      VARCHAR(500),
    avg_rating      NUMERIC(3,2) DEFAULT 0.0 CHECK (avg_rating BETWEEN 0 AND 10),
    rating_count    INTEGER DEFAULT 0,
    metadata        JSONB DEFAULT '{}'::jsonb,    -- cast, keywords, tags, awards
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_movies_title_trgm ON movies USING gin (title gin_trgm_ops); -- for search
CREATE INDEX idx_movies_active     ON movies (is_active);
CREATE INDEX idx_movies_metadata   ON movies USING gin (metadata);

-- Many-to-many: movie ↔ genre ------------------------------------------
CREATE TABLE movie_genres (
    movie_id        UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    genre_id        UUID NOT NULL REFERENCES genres(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (movie_id, genre_id)
);

-- Halls ----------------------------------------------------------------
CREATE TABLE halls (
    hall_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(60) NOT NULL UNIQUE,
    total_seats     INTEGER NOT NULL CHECK (total_seats > 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seats belong to a hall (a Showtime inherits the hall's seats) --------
CREATE TABLE seats (
    seat_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hall_id         UUID NOT NULL REFERENCES halls(hall_id) ON DELETE CASCADE,
    row_label       VARCHAR(3) NOT NULL,    -- 'A', 'B', ..., 'AA'
    seat_number     INTEGER NOT NULL CHECK (seat_number > 0),
    seat_type       VARCHAR(20) NOT NULL DEFAULT 'STANDARD'
                    CHECK (seat_type IN ('STANDARD', 'PREMIUM', 'ACCESSIBLE')),
    UNIQUE (hall_id, row_label, seat_number)
);
CREATE INDEX idx_seats_hall ON seats (hall_id);

-- Showtimes ------------------------------------------------------------
CREATE TABLE showtimes (
    showtime_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id        UUID NOT NULL REFERENCES movies(movie_id) ON DELETE RESTRICT,
    hall_id         UUID NOT NULL REFERENCES halls(hall_id)   ON DELETE RESTRICT,
    start_time      TIMESTAMPTZ NOT NULL,
    end_time        TIMESTAMPTZ NOT NULL,
    price           NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (end_time > start_time)
);
CREATE INDEX idx_showtimes_movie_start  ON showtimes (movie_id, start_time);
CREATE INDEX idx_showtimes_hall_start   ON showtimes (hall_id, start_time);

-- Prevent overlapping showtimes in the same hall (FR-18 test-17) -------
-- Uses a GiST exclusion constraint with tstzrange.
ALTER TABLE showtimes ADD CONSTRAINT no_hall_overlap
  EXCLUDE USING gist (
    hall_id WITH =,
    tstzrange(start_time, end_time, '[)') WITH &&
  ) WHERE (is_active);

-- =====================================================================
-- BOOKINGS
-- =====================================================================
-- One row per booked seat. Multi-seat purchases share a booking_group_id.
CREATE TABLE bookings (
    booking_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_group_id  UUID NOT NULL,    -- groups seats purchased together
    user_id           UUID NOT NULL REFERENCES users(user_id)     ON DELETE RESTRICT,
    showtime_id       UUID NOT NULL REFERENCES showtimes(showtime_id) ON DELETE RESTRICT,
    seat_id           UUID NOT NULL REFERENCES seats(seat_id)     ON DELETE RESTRICT,
    status            VARCHAR(20) NOT NULL DEFAULT 'PENDING'
                      CHECK (status IN ('PENDING','CONFIRMED','CANCELLED','USED','EXPIRED')),
    price_paid        NUMERIC(10,2) NOT NULL,
    qr_token          VARCHAR(128) UNIQUE,    -- opaque token, set at CONFIRMED
    payment_token     VARCHAR(128),           -- token returned by Payment GW
    hold_expires_at   TIMESTAMPTZ,            -- used while status='PENDING'
    booked_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confirmed_at      TIMESTAMPTZ,
    cancelled_at      TIMESTAMPTZ,
    used_at           TIMESTAMPTZ,
    UNIQUE (showtime_id, seat_id)    -- one active booking per seat per showtime
                                     -- NB: Cancelled rows also block re-booking;
                                     -- see §6.11 for the soft-delete workaround.
);
CREATE INDEX idx_bookings_user_status   ON bookings (user_id, status);
CREATE INDEX idx_bookings_group         ON bookings (booking_group_id);
CREATE INDEX idx_bookings_qr            ON bookings (qr_token);
CREATE INDEX idx_bookings_hold_expiry   ON bookings (hold_expires_at) WHERE status = 'PENDING';

-- IMPORTANT: the UNIQUE(showtime_id, seat_id) above is too strict because
-- a cancelled seat must be rebookable. We use a PARTIAL UNIQUE INDEX instead:
ALTER TABLE bookings DROP CONSTRAINT bookings_showtime_id_seat_id_key;
CREATE UNIQUE INDEX uniq_active_seat_per_showtime
  ON bookings (showtime_id, seat_id)
  WHERE status IN ('PENDING','CONFIRMED','USED');

-- =====================================================================
-- RATINGS (FR coverage: supports avg_rating on movies)
-- =====================================================================
CREATE TABLE user_ratings (
    rating_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(user_id)   ON DELETE CASCADE,
    movie_id        UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    score           INTEGER NOT NULL CHECK (score BETWEEN 1 AND 10),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, movie_id)
);
CREATE INDEX idx_ratings_movie ON user_ratings (movie_id);

-- =====================================================================
-- NOTIFICATIONS
-- =====================================================================
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    type            VARCHAR(40) NOT NULL,     -- 'BOOKING_CONFIRM','BOOKING_CANCEL','RECOMMENDATION'
    channel         VARCHAR(10) NOT NULL CHECK (channel IN ('EMAIL','SMS','IN_APP')),
    subject         VARCHAR(255),
    body            TEXT NOT NULL,
    related_booking_id UUID REFERENCES bookings(booking_id) ON DELETE SET NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'PENDING'
                    CHECK (status IN ('PENDING','SENT','FAILED','DELIVERED')),
    retry_count     INTEGER NOT NULL DEFAULT 0,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at         TIMESTAMPTZ
);
CREATE INDEX idx_notif_user_unread ON notifications (user_id, is_read);
CREATE INDEX idx_notif_pending     ON notifications (status) WHERE status IN ('PENDING','FAILED');

-- =====================================================================
-- RECOMMENDATION SUPPORT
-- =====================================================================
-- Log of served recommendations (for debugging, not for scoring) -------
CREATE TABLE recommendation_history (
    rec_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    movie_id        UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    algorithm       VARCHAR(20) NOT NULL,  -- 'CBF', 'POPULARITY'
    relevance_score NUMERIC(4,3),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_rec_user_created ON recommendation_history (user_id, created_at DESC);

-- Materialized view: pairwise movie cosine similarity over genre vector
-- Refreshed nightly by rec_similarity_refresh job.
CREATE MATERIALIZED VIEW mv_movie_similarity AS
  SELECT ... ;  -- Concrete SQL is given in §6.4

-- =====================================================================
-- ADMIN ACTION LOG (audit trail for FR-17..FR-20)
-- =====================================================================
CREATE TABLE admin_actions (
    action_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id   UUID NOT NULL REFERENCES users(user_id),
    action_type     VARCHAR(40) NOT NULL,   -- 'ADD_MOVIE','SUSPEND_USER',...
    target_type     VARCHAR(40),            -- 'MOVIE','USER','SHOWTIME'
    target_id       UUID,
    payload         JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_admin_actions_actor ON admin_actions (actor_user_id, created_at DESC);
```

### 4.3 Extensions required

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- idx_movies_title_trgm (for search)
CREATE EXTENSION IF NOT EXISTS btree_gist; -- exclusion constraint on showtimes
```

### 4.4 Seed data (required before first run)

- Genres: `Action, Adventure, Animation, Comedy, Crime, Documentary, Drama, Family, Fantasy, Horror, Mystery, Romance, Sci-Fi, Thriller, War, Western` (16 rows).
- One Admin user: from environment variables `CINELUX_ADMIN_EMAIL` and `CINELUX_ADMIN_PASSWORD`.
- One Hall for smoke-testing: `Hall A`, 100 seats (10 rows × 10 seats).

---

## 5. Authentication, Authorization, Sessions

### 5.1 Authentication

- **Scheme:** JWT bearer tokens via `djangorestframework-simplejwt`.
- **Access token lifetime:** 60 minutes.
- **Refresh token lifetime:** 7 days. Refresh rotates on use.
- **Password hashing:** Django's default `PBKDF2` is acceptable (NFR-02 says "BCrypt" but PBKDF2 with SHA-256 at Django's default 600k iterations meets the spirit of NFR-02). If the team chooses BCrypt, configure it via `PASSWORD_HASHERS` — see §12.2.
- **Transport:** HTTPS only. Reject HTTP in production via nginx redirect.
- **Token contents:** `user_id`, `role`, `exp`, `iat`. Nothing else — no PII.

### 5.2 Authorization

Every API endpoint declares its required role via a DRF permission class:

| Permission | Who |
|---|---|
| `AllowAny` | register, login |
| `IsAuthenticated` | default for everything else |
| `IsOwnerOrAdmin` | user profile, user bookings (`user_id` in path must match token subject, OR role=ADMIN) |
| `IsAdmin` | all `/api/admin/**` endpoints |
| `IsStaffOrAdmin` | ticket validation (`/api/validate/**`) |

### 5.3 Role model

Per CINELUX-CONST-09, we have **two primary roles: USER and ADMIN**. Gate Staff is modelled as a third `STAFF` role in the DB (see `users.role` CHECK), because FR-15/FR-16 are scoped narrower than ADMIN — staff should not be able to add movies or manage accounts. This does not violate the constraint because STAFF is not "an intermediate role in the authorisation hierarchy" — it's a sibling role with a narrow, distinct permission set. Document this in the design justification.

### 5.4 Session invalidation

- **Password change** → invalidate all refresh tokens for that user (implement by incrementing a `token_version` column on `users` and checking it in a custom JWT authentication class).
- **Account suspension** (FR-19) → same mechanism; also reject new logins with `AUTH-003 Account Suspended`.

---

*(continued in next section)*

---

## 6. Functional Requirements — Implementation Detail

This section defines every FR end-to-end. Each FR includes: the endpoint, the flow, the business rules, the data touched, the design decisions, and the test cases.

**Base URL:** `/api` (all paths below are relative to this).

### 6.1 FR-01 · Browse Movie Catalogue

| Attribute | Value |
|---|---|
| Use Case | UC-01 Browse catalogue |
| Priority | MUST |
| Test Case | TC-01 |
| API | `GET /api/movies` |
| Auth | `AllowAny` (browse is public for MVP; login is required to book) |

**Request (query string):**

| Param | Type | Required | Default | Notes |
|---|---|---|---|---|
| `page` | integer | no | 1 | 1-indexed |
| `limit` | integer | no | 20 | max 100 |
| `status` | string | no | `showing` | `showing` = movies with ≥1 future showtime; `upcoming` = `release_date > NOW()`; `all` |

**Response 200:**
```json
{
  "page": 1,
  "limit": 20,
  "totalCount": 87,
  "movies": [
    {
      "movieId": "mov_abc123",
      "title": "Dune: Part Three",
      "genre": ["Sci-Fi", "Adventure"],
      "language": "English",
      "ageRating": "PG-13",
      "rating": 8.4,
      "posterUrl": "https://cdn.cinema.io/posters/...",
      "durationMinutes": 155,
      "nextShowtime": "2026-04-20T19:30:00Z"
    }
  ]
}
```

**Flow:**

1. API validates query params (`page`, `limit`).
2. `CatalogueService.browse(status, page, limit)` runs.
3. Repository issues one SQL query:
   ```sql
   SELECT m.*, array_agg(g.name) AS genre,
          MIN(s.start_time) FILTER (WHERE s.start_time > NOW()) AS next_showtime
     FROM movies m
     LEFT JOIN movie_genres mg ON mg.movie_id = m.movie_id
     LEFT JOIN genres g       ON g.genre_id = mg.genre_id
     LEFT JOIN showtimes s    ON s.movie_id = m.movie_id AND s.is_active
    WHERE m.is_active
      AND (/* status filter */)
    GROUP BY m.movie_id
    ORDER BY next_showtime NULLS LAST, m.title
    LIMIT :limit OFFSET (:page - 1) * :limit;
   ```
4. Service returns `{totalCount, movies}`.

**Rules:**
- Soft-deleted movies (`is_active = false`) must not appear.
- If a movie has no future showtimes but `status=showing`, exclude it.

**Data touched:** `movies` (read), `movie_genres` (read), `genres` (read), `showtimes` (read).

**Design decisions:**
- Pagination is **offset-based**. Acceptable for catalogues in the low hundreds; revisit if the catalogue exceeds 10k rows.
- We do not cache this endpoint (CINELUX-CONST-07). Performance target (NFR-01, ≤ 2s under load) is met by the composite index on `showtimes(movie_id, start_time)` and `pg_trgm` on titles.

---

### 6.2 FR-02 · Filter Movies by Genre & Date

| Attribute | Value |
|---|---|
| Use Case | UC-01 Browse catalogue |
| Priority | MUST |
| Test Case | TC-02 |
| API | `GET /api/movies` (same endpoint as FR-01, with filter params) |

**Request (additional query string params):**

| Param | Type | Required | Notes |
|---|---|---|---|
| `genre` | string | no | Genre name. Exact match on `genres.name`. |
| `date` | ISO-8601 date | no | Only movies with ≥1 showtime starting on this calendar date (cinema's local TZ). |
| `language` | string | no | Exact match. |
| `ageRating` | string | no | Exact match. |
| `q` | string | no | Free-text title search (trigram similarity; FR-03's search bar uses this param). |

**Flow:**

1. Same entry point as FR-01. The Service extends the WHERE clause dynamically:
   - `genre` → `EXISTS (SELECT 1 FROM movie_genres mg JOIN genres g ON g.genre_id=mg.genre_id WHERE mg.movie_id=m.movie_id AND g.name = :genre)`
   - `date` → `EXISTS (SELECT 1 FROM showtimes s WHERE s.movie_id=m.movie_id AND DATE(s.start_time AT TIME ZONE 'Asia/Amman') = :date AND s.is_active)` — the exact timezone is a configuration value `CINEMA_TIMEZONE` (default `UTC` in dev, `Asia/Amman` in prod per the team's location).
   - `language`, `ageRating` → direct column filters on `movies`.
   - `q` → `m.title % :q AND similarity(m.title, :q) > 0.2` (pg_trgm); order by similarity DESC.
2. Same response shape as FR-01.

**Rules:**
- Filters combine with AND.
- Unknown genre names return an empty list (not an error).

**Data touched:** same as FR-01.

**Design decisions:**
- We collapse browse (FR-01), filter (FR-02), details-list, and search (FR-03 partial) into one endpoint. This is deliberate: the React grid page calls one endpoint with different query strings as the user types/selects. It reduces API surface and keeps the UI code simple.

---

### 6.3 FR-03 · View Movie Details & Showtimes

| Attribute | Value |
|---|---|
| Use Case | UC-01 |
| Priority | MUST |
| Test Case | TC-03 |
| APIs | `GET /api/movies/{movieId}` and `GET /api/movies/{movieId}/showtimes` |

**Why two endpoints?** The details page first loads the movie metadata, then (often asynchronously) the showtimes list with filters.

#### 6.3.1 `GET /api/movies/{movieId}`

**Response 200:**
```json
{
  "movieId": "mov_abc123",
  "title": "Dune: Part Three",
  "description": "Paul Atreides continues...",
  "durationMinutes": 155,
  "releaseDate": "2026-12-18",
  "language": "English",
  "ageRating": "PG-13",
  "rating": 8.4,
  "ratingCount": 1203,
  "posterUrl": "https://cdn.cinema.io/posters/mov_abc123.jpg",
  "genre": ["Sci-Fi","Adventure"],
  "metadata": {
    "cast": ["Timothée Chalamet","Zendaya"],
    "keywords": ["desert","empire","prophecy"],
    "tags": ["epic","space-opera"]
  }
}
```

**Flow:**
1. Validate `movieId` is a UUID (else `GEN-400`).
2. `CatalogueService.getDetails(movieId)`.
3. Repo returns movie row + genres join. Raise `MOV-404` if not found or `is_active=false`.
4. Return the full object (including `metadata` JSONB, flattened as above).

#### 6.3.2 `GET /api/movies/{movieId}/showtimes`

**Query params:** `date` (ISO date, optional), `hall` (hall_id, optional).

**Response 200:**
```json
{
  "movieId": "mov_abc123",
  "showtimes": [
    {
      "showtimeId": "sho_001",
      "hallId": "hal_03",
      "hallName": "Hall 3",
      "startTime": "2026-04-20T19:30:00Z",
      "endTime": "2026-04-20T22:05:00Z",
      "totalSeats": 120,
      "availableSeats": 43,
      "price": 12.00,
      "currency": "USD"
    }
  ]
}
```

**Flow:**
1. Validate `movieId`. Raise `MOV-404` if missing.
2. `CatalogueService.getShowtimes(movieId, date, hallId)`.
3. Repo joins `showtimes` → `halls`, counts `availableSeats` as `hall.total_seats - COUNT(bookings WHERE showtime_id=s.showtime_id AND status IN ('PENDING','CONFIRMED','USED'))`.
4. Exclude showtimes that have already started: `start_time > NOW()`.

**Data touched:** `movies`, `showtimes`, `halls`, `bookings` (count only).

**Design decisions:**
- `availableSeats` is computed on every request. This is fine for the single-VM, low-traffic use case. If NFR-08 (5000 concurrent users) proves tight, add a lightweight trigger that maintains a `showtimes.available_seats` counter.

---

### 6.4 FR-04 · Personalised Movie Recommendations

| Attribute | Value |
|---|---|
| Use Case | UC-01.1 |
| Priority | SHOULD |
| Test Case | TC-04 |
| API | `GET /api/recommendations/{userId}` |
| Auth | `IsOwnerOrAdmin` |

**Request query params:**
- `limit` (int, default 10, max 50)
- `genre` (string, optional — constrain to a genre)

**Response 200:**
```json
{
  "userId": "usr_9f4a2b1c",
  "algorithm": "CBF",
  "coldStart": false,
  "recommendations": [
    {
      "movieId": "mov_abc123",
      "title": "Dune: Part Three",
      "genre": ["Sci-Fi","Adventure"],
      "rating": 8.4,
      "posterUrl": "...",
      "relevanceScore": 0.94,
      "reason": "Based on your interest in Sci-Fi and past bookings"
    }
  ]
}
```

**Algorithm: Content-Based Filtering (CBF).** *Not* CF, despite the Task 4 doc mentioning both. Rationale in §12.5.

**Flow (Service layer: `RecommendationService.recommend(userId, limit, genre)`):**

1. **Build user preference vector `u`:**
   - Fetch `user_genre_preferences` for the user → set `u[g] = 1` for each preferred genre.
   - Fetch the user's booking history (last 90 days, status IN CONFIRMED/USED) → for each booked movie, increment `u[g]` for each of its genres.
   - Fetch user ratings → for each rated movie with `score >= 7`, increment `u[g]` for each genre.
   - Normalize `u` to unit length (L2 norm).
2. **Determine cold-start:** `coldStart = (user has 0 bookings AND 0 ratings)`. If cold-start:
   - If `u` is empty (no preferred genres either), fall back to **popularity** (top-rated movies with ≥50 ratings or the top 10 by booking count in the last 30 days). Set `algorithm = 'POPULARITY'`, `coldStart = true`, `relevanceScore = null`, `reason = "Popular this week"`.
3. **Build candidate set:** all active movies with ≥1 future showtime, excluding movies already booked by the user (`status != CANCELLED`).
4. **Score each candidate `m`:**
   - Build movie genre vector `v_m` from `movie_genres`.
   - `score = cosine(u, v_m)`.
   - Optional: weight by `m.avg_rating / 10`.
5. **Optionally constrain by genre** (if `genre` query param given) before scoring.
6. **Sort by score DESC, take top `limit`.**
7. **Generate `reason`:** pick the top 2 genres by `u[g]` intersected with the candidate's genres; render as "Based on your interest in {g1} and {g2}". If no intersection, "Based on your booking history".
8. **Log** each returned recommendation to `recommendation_history`.
9. **Return** the list.

**Implementation notes:**
- The CBF can be expressed in pure SQL using the **materialized view `mv_movie_similarity`** (refreshed nightly by `rec_similarity_refresh`). Build the view as:
   ```sql
   CREATE MATERIALIZED VIEW mv_movie_similarity AS
   WITH movie_genre_vec AS (
     SELECT m.movie_id, array_agg(mg.genre_id ORDER BY mg.genre_id) AS genres
     FROM movies m
     LEFT JOIN movie_genres mg ON mg.movie_id = m.movie_id
     GROUP BY m.movie_id
   )
   SELECT
     a.movie_id AS movie_a,
     b.movie_id AS movie_b,
     /* cosine = |intersection| / sqrt(|A| * |B|) */
     cardinality(array(SELECT unnest(a.genres) INTERSECT SELECT unnest(b.genres)))::float
       / GREATEST(sqrt(cardinality(a.genres) * cardinality(b.genres)), 1)
       AS sim
   FROM movie_genre_vec a
   JOIN movie_genre_vec b ON a.movie_id < b.movie_id;
   CREATE INDEX idx_mv_sim_a ON mv_movie_similarity (movie_a, sim DESC);
   CREATE INDEX idx_mv_sim_b ON mv_movie_similarity (movie_b, sim DESC);
   ```
- However, for **user → candidate movies** scoring (not movie → movie), Python scikit-learn is simpler and fast enough. Implement with `sklearn.metrics.pairwise.cosine_similarity` over a ~50-movie catalogue and a ~16-genre vector — well under 50ms.

**Error handling:**
- Engine exception → return `REC-500` **with fallback popularity list** (do not error-out the UI; log and return `{algorithm: 'POPULARITY', recommendations: [...]}` with HTTP 200). This honours CINELUX-CONST-11 (defensive fallback).

**Data touched:** `users`, `user_genre_preferences`, `user_ratings`, `bookings`, `movies`, `movie_genres`, `genres`, `recommendation_history` (write).

**Design decisions:**
- **CBF only, not CF.** Simpler; no cold-start failure; no pre-computation of a user-user similarity matrix (which would violate the single-store constraint if we needed to cache it).
- **Popularity fallback** covers cold-start + engine failure + empty-catalogue cases.
- **`recommendation_history`** is for offline evaluation, not for runtime filtering (we don't remove a movie from future recommendations because it was previously shown — the score is still the score).

---

### 6.5 FR-05 · Trending & Popular Movies Feed

| Attribute | Value |
|---|---|
| Use Case | UC-01.1 |
| Priority | SHOULD |
| Test Case | TC-05 |
| API | `GET /api/movies/trending` |
| Auth | `AllowAny` |

**Response:** same shape as FR-01 (list of movie summaries).

**Flow:**
1. `CatalogueService.trending(limit=10)`.
2. Query:
   ```sql
   SELECT m.*, COUNT(b.booking_id) AS booking_count
     FROM movies m
     JOIN showtimes s ON s.movie_id = m.movie_id
     JOIN bookings  b ON b.showtime_id = s.showtime_id
                    AND b.status IN ('CONFIRMED','USED')
                    AND b.created_at > NOW() - INTERVAL '7 days'
    WHERE m.is_active
    GROUP BY m.movie_id
    ORDER BY booking_count DESC
    LIMIT :limit;
   ```

**Rules:**
- Rolling **7-day window** for "trending". Can be tuned later.
- If fewer than `limit` movies have any bookings in 7 days, pad with top-rated movies (by `avg_rating`).

**Data touched:** `movies`, `showtimes`, `bookings`.

---

### 6.6 FR-06 · Select Seats Interactively

| Attribute | Value |
|---|---|
| Use Case | UC-02 |
| Priority | MUST |
| Test Case | TC-06 |
| APIs | `GET /api/showtimes/{showtimeId}/seats` (seat map) + `POST /api/bookings/hold` (temporary hold) |
| Auth | `IsAuthenticated` |

This FR is the **critical-path concurrency hotspot**. Read carefully.

#### 6.6.1 `GET /api/showtimes/{showtimeId}/seats` — fetch the seat map

**Response 200:**
```json
{
  "showtimeId": "sho_001",
  "hallId": "hal_03",
  "hallName": "Hall 3",
  "price": 12.00,
  "currency": "USD",
  "seats": [
    { "seatId": "set_A01", "row": "A", "number": 1, "type": "STANDARD", "status": "AVAILABLE" },
    { "seatId": "set_A02", "row": "A", "number": 2, "type": "STANDARD", "status": "BOOKED" },
    { "seatId": "set_A03", "row": "A", "number": 3, "type": "STANDARD", "status": "HELD" },
    ...
  ]
}
```

**`status`** is derived from the join with `bookings`:
- `AVAILABLE` = no row in `bookings` for this `(showtime_id, seat_id)` with status in PENDING/CONFIRMED/USED.
- `HELD` = exists a row with status=`PENDING` and `hold_expires_at > NOW()`.
- `BOOKED` = exists a row with status in (`CONFIRMED`, `USED`).

**Flow:**
1. Validate `showtimeId` (else `SHOW-404`).
2. Repo query:
   ```sql
   SELECT s.seat_id, s.row_label, s.seat_number, s.seat_type,
          CASE
            WHEN b.status IN ('CONFIRMED','USED') THEN 'BOOKED'
            WHEN b.status = 'PENDING' AND b.hold_expires_at > NOW() THEN 'HELD'
            ELSE 'AVAILABLE'
          END AS status
     FROM seats s
     JOIN showtimes st ON st.hall_id = s.hall_id
     LEFT JOIN bookings b ON b.seat_id = s.seat_id
                         AND b.showtime_id = st.showtime_id
                         AND b.status IN ('PENDING','CONFIRMED','USED')
    WHERE st.showtime_id = :showtimeId
    ORDER BY s.row_label, s.seat_number;
   ```

#### 6.6.2 `POST /api/bookings/hold` — place a temporary hold

**Purpose:** when the user selects seats and clicks "Continue to payment", we lock those seats for up to **10 minutes** so another user cannot grab them mid-payment. *Without this step, two users could both reach the payment screen with the same seats and the second one to pay would get SEAT-409, which is a bad UX.*

**Request:**
```json
{
  "userId": "usr_...",
  "showtimeId": "sho_001",
  "seatIds": ["set_A01","set_A02"]
}
```

**Response 201:**
```json
{
  "bookingGroupId": "grp_x1y2z3",
  "showtimeId": "sho_001",
  "seats": ["set_A01","set_A02"],
  "status": "PENDING",
  "holdExpiresAt": "2026-04-14T19:40:00Z",
  "totalAmount": 24.00,
  "currency": "USD"
}
```

**Flow (Service — `BookingService.holdSeats`) — runs in a transaction:**

1. Validate `userId == token.subject` (or role=ADMIN).
2. Validate `showtimeId` exists, is_active, and `start_time > NOW()` (else `SHOW-404` or `BOOK-422 Showtime already started`).
3. Validate each seatId belongs to the showtime's hall.
4. **Lock the relevant booking rows** for these seats under this showtime:
   ```python
   # Django ORM
   with transaction.atomic():
       existing = (Booking.objects
                   .select_for_update()
                   .filter(showtime_id=showtime_id,
                           seat_id__in=seat_ids,
                           status__in=['PENDING','CONFIRMED','USED']))
       # Release expired PENDING holds in-line:
       existing_active = [b for b in existing
                          if b.status != 'PENDING' or b.hold_expires_at > timezone.now()]
       if existing_active:
           raise SeatUnavailableError(seat_ids=[b.seat_id for b in existing_active])
   ```
   If any seat is still actively held/booked: raise `SEAT-409` with the list of offending seat IDs.
5. **Insert new rows** with `status='PENDING'`, `hold_expires_at = NOW() + 10 minutes`, `booking_group_id = new UUID`, `price_paid = showtime.price`. One row per seat.
6. Commit.
7. Return the booking group info.

**Design decisions — WHY it is safe:**
- PostgreSQL's `SELECT ... FOR UPDATE` serializes concurrent transactions touching the same rows. Two simultaneous holds on the same seat will see one winner; the loser sees the winner's row and raises `SEAT-409`.
- `uniq_active_seat_per_showtime` (the partial unique index from §4.2) is a **second line of defence** — even without `FOR UPDATE`, PostgreSQL would reject the second insert.
- The **10-minute hold** is configurable (`BOOKING_HOLD_MINUTES`). It's a business-UX knob, not a correctness one.

**Data touched:** `showtimes` (read), `seats` (read), `bookings` (read + write).

---

### 6.7 FR-07 · Process Online Payment

| Attribute | Value |
|---|---|
| Use Case | UC-02 |
| Priority | MUST |
| Test Case | TC-07 |
| API | `POST /api/bookings/confirm` |
| Auth | `IsAuthenticated` |

**Request:**
```json
{
  "bookingGroupId": "grp_x1y2z3",
  "paymentMethod": {
    "type": "CARD",
    "token": "tok_abcxyz"    // opaque token from the gateway's JS SDK
  }
}
```

**Critical:** Cinélux never sees raw card numbers (CINELUX-CONST-12). The React app tokenizes the card client-side via the Payment Gateway's JS SDK, and we get back an opaque token.

**Response 201:**
```json
{
  "bookingGroupId": "grp_x1y2z3",
  "userId": "usr_...",
  "showtimeId": "sho_001",
  "movieTitle": "Dune: Part Three",
  "seats": ["A1","A2"],
  "status": "CONFIRMED",
  "totalAmount": 24.00,
  "currency": "USD",
  "paymentToken": "PAY-SIM-99821",
  "qrCodeToken": "QR-grp_x1y2z3-2026041419300",
  "qrCodeUrl": "https://cdn.cinema.io/qr/grp_x1y2z3.png",
  "confirmedAt": "2026-04-14T19:30:00Z"
}
```

**Flow (`BookingService.confirm` — single atomic transaction):**

1. Load all `bookings` rows for `bookingGroupId` with `select_for_update()`. Raise `BOOK-404` if empty.
2. Verify ownership (`user_id == token.subject`) → else `GEN-403`.
3. Verify all rows are `status = 'PENDING'` AND `hold_expires_at > NOW()` → else `BOOK-410 Hold expired`.
4. Compute `totalAmount = sum(price_paid)`.
5. **Call Payment Gateway** (see §8.1):
   ```python
   result = payment_gateway.charge(
       token=request.paymentMethod.token,
       amount=total_amount, currency='USD',
       idempotency_key=booking_group_id   # critical
   )
   ```
   Timeout 10s. If the gateway returns non-success:
   - `DECLINED` → roll back; return `PAY-402 Payment declined` with gateway's reason code.
   - Timeout or 5xx → roll back; return `PAY-503 Payment gateway unavailable`. Seats remain PENDING and will expire naturally.
6. For each booking row:
   - `status = 'CONFIRMED'`
   - `confirmed_at = NOW()`
   - `payment_token = result.transaction_id`
   - `qr_token = generate_qr_token(booking_group_id)` — see §6.8 for the token spec.
7. **Generate the QR image** (FR-08) and **send confirmation notification** (FR-08) — both happen inside the same transaction, *but notification failure does not roll back the booking* (see §8.2).
8. Commit.
9. Return.

**Idempotency:**
- The `idempotency_key = booking_group_id` passed to the Payment Gateway means if the client retries `POST /bookings/confirm` after a network blip, we don't double-charge. The gateway returns the same `transaction_id`.
- On the Cinélux side, if the transaction has already been confirmed and the client retries, detect the `status='CONFIRMED'` state and return the existing booking with HTTP 200 (not 201).

**Payment Gateway simulation (CINELUX-CONST-11):**
- In dev/test, the gateway is a stub that:
  - Returns `SUCCESS` for tokens starting with `tok_good_`.
  - Returns `DECLINED` for tokens starting with `tok_bad_`.
  - Sleeps 12s (timeout) for tokens starting with `tok_slow_`.
- In production (academic deployment), replace the stub with the real gateway's SDK — code-level change only.

**Data touched:** `bookings` (select_for_update + update), `notifications` (insert).

**Design decisions:**
- Payment is synchronous because CINELUX-CONST-08 forbids message queues. The 10s timeout is generous; real gateways respond in < 2s.
- We store the gateway's `transaction_id` on each seat's booking row so refunds (FR-11) can target it.

---

### 6.8 FR-08 · Generate & Send E-Ticket (QR)

| Attribute | Value |
|---|---|
| Use Case | UC-02 |
| Priority | MUST |
| Test Case | TC-08 |
| No separate endpoint — executed inside FR-07's `confirm` |

**Token spec:**
- `qr_token = f"QR-{booking_group_id}-{unix_ms}"`
- Opaque string, stored in `bookings.qr_token` (UNIQUE).
- **Not** a JWT. Scanning the QR → the raw token → a lookup against the DB. Simple and revocable.

**QR image generation:**
- Library: `qrcode` (Python, pure-Python, no system deps).
- Write to local filesystem under `/var/www/cinelux/qr/{booking_group_id}.png`.
- nginx serves `/qr/*` statically.
- `qrCodeUrl = f"{PUBLIC_BASE_URL}/qr/{booking_group_id}.png"`.

**Flow:**
1. Compose payload: **only the token**, not the booking details. (Privacy — a leaked QR image must not reveal PII.)
2. `img = qrcode.make(qr_token); img.save(path)`.
3. Update `bookings.qr_token` and return `qrCodeUrl`.

**Notification (same FR):**
- `NotificationService.sendBookingConfirmation(bookingGroupId)` is invoked AFTER the DB commit of the confirm transaction.
- **Why after commit?** If the notification call fails mid-transaction, we don't want to lose the booking. We use a Django `transaction.on_commit(lambda: ...)` hook.
- Notification:
  - Channel: EMAIL by default (SMS if the user has a phone number AND opted-in — not in MVP).
  - Subject: `Booking confirmed — {movie_title} on {start_time}`.
  - Body: plaintext with movie title, showtime, hall, seats, a link to the ticket, and the QR image as an inline attachment.
  - Insert a row into `notifications` with `status='PENDING'` first, then call the external service, then update to `SENT` or `FAILED`.

**Data touched:** `bookings` (update qr_token), `notifications` (insert + update), filesystem (QR image).

---

### 6.9 FR-09 · View Booking History

| Attribute | Value |
|---|---|
| Use Case | UC-03 |
| Priority | MUST |
| Test Case | TC-09 |
| API | `GET /api/bookings?userId={userId}` |
| Auth | `IsOwnerOrAdmin` |

**Query params:**
- `userId` (required; must match token or role=ADMIN)
- `status` (optional: `CONFIRMED`, `CANCELLED`, `USED`, `PAST`, `UPCOMING`)
- `page`, `limit`

**Response 200:**
```json
{
  "page": 1, "total": 4,
  "bookings": [
    {
      "bookingGroupId": "grp_x1y2z3",
      "movieTitle": "Dune: Part Three",
      "posterUrl": "...",
      "showtime": {
        "showtimeId": "sho_001",
        "startTime": "2026-04-20T19:30:00Z",
        "hallName": "Hall 3"
      },
      "seats": ["A1","A2"],
      "status": "CONFIRMED",
      "totalAmount": 24.00,
      "qrCodeUrl": "...",
      "createdAt": "2026-04-14T19:30:00Z"
    }
  ]
}
```

**Note:** The response groups per `booking_group_id`, not per seat. Multi-seat bookings are presented as a single card in the UI.

**Flow:**
1. Authorise.
2. Repo query: group by `booking_group_id`, aggregate seat list:
   ```sql
   SELECT b.booking_group_id,
          MIN(b.created_at)                    AS created_at,
          MIN(b.status)                        AS status,  -- all seats share status
          SUM(b.price_paid)                    AS total_amount,
          array_agg(s.row_label || s.seat_number ORDER BY s.row_label, s.seat_number) AS seats,
          MIN(b.qr_token)                      AS qr_token,
          m.title AS movie_title, m.poster_url,
          st.showtime_id, st.start_time, h.name AS hall_name
     FROM bookings b
     JOIN seats s      ON s.seat_id = b.seat_id
     JOIN showtimes st ON st.showtime_id = b.showtime_id
     JOIN movies m     ON m.movie_id = st.movie_id
     JOIN halls h      ON h.hall_id = st.hall_id
    WHERE b.user_id = :userId
      AND (:status IS NULL OR b.status = :status)
    GROUP BY b.booking_group_id, m.title, m.poster_url,
             st.showtime_id, st.start_time, h.name
    ORDER BY st.start_time DESC
    LIMIT :limit OFFSET :offset;
   ```
3. For `status=UPCOMING` add `AND st.start_time > NOW() AND b.status='CONFIRMED'`. For `PAST`, `AND (st.start_time < NOW() OR b.status IN ('USED','CANCELLED'))`.

**Data touched:** `bookings`, `seats`, `showtimes`, `movies`, `halls`.

---

### 6.10 FR-10 · View Upcoming Booking Details

| Attribute | Value |
|---|---|
| Use Case | UC-03 |
| Priority | MUST |
| Test Case | TC-10 |
| API | `GET /api/bookings/{bookingGroupId}` |
| Auth | `IsOwnerOrAdmin` |

**Flow:**
1. Fetch all `bookings` rows for the group. Raise `BOOK-404` if empty.
2. Authorise (owner or admin).
3. Same projection as FR-09, but single item.

**Response 200:** same shape as a single item in FR-09's list, plus:
- `qrCodeUrl` (always present for CONFIRMED).
- `cancellable` (boolean): `true` iff `status=CONFIRMED AND showtime.start_time - NOW() > 2 hours` (see §6.11 cancellation policy).
- `cancellationRefundEligible` (boolean, see §6.11).

---

### 6.11 FR-11 · Cancel Booking & Request Refund

| Attribute | Value |
|---|---|
| Use Case | UC-04 |
| Priority | MUST |
| Test Case | TC-11 |
| API | `DELETE /api/bookings/{bookingGroupId}` |
| Auth | `IsOwnerOrAdmin` |

**Cancellation policy (FR-12 enforced here):**

| Time before showtime | Cancellation allowed? | Refund amount |
|---|---|---|
| ≥ 24 hours | Yes | 100% of `totalAmount` |
| 2–24 hours | Yes | 50% of `totalAmount` |
| < 2 hours | **No** — return `BOOK-403 Cancellation window closed` |
| Already USED | **No** — `BOOK-403 Ticket already used` |
| Already CANCELLED | Idempotent — return current state with HTTP 200 |

**Flow (`BookingService.cancel`):**

1. Load booking rows for the group with `select_for_update()`. Raise `BOOK-404`.
2. Authorise.
3. Compute the refund policy from `showtime.start_time - NOW()`.
4. If not allowed → raise `BOOK-403` with the specific reason (`WINDOW_CLOSED`, `ALREADY_USED`).
5. If already CANCELLED → return 200 with current state (idempotent).
6. Update each row: `status='CANCELLED'`, `cancelled_at=NOW()`. The `uniq_active_seat_per_showtime` index now permits re-booking these seats.
7. **Issue refund** via Payment Gateway — `payment_gateway.refund(transaction_id=..., amount=refund_amount, idempotency_key=booking_group_id)`. On failure, log and queue retry (do NOT fail the cancellation — customer gets their seat released, refund is pursued asynchronously).
8. On `transaction.on_commit`, enqueue the cancellation notification.
9. Return:

```json
{
  "bookingGroupId": "grp_x1y2z3",
  "status": "CANCELLED",
  "refundAmount": 12.00,
  "refundCurrency": "USD",
  "cancelledAt": "2026-04-15T08:00:00Z",
  "seatsReleased": ["A12","A13"]
}
```

**Design decisions:**
- Refund is **best-effort**. We always succeed the cancellation; the refund call is idempotent by `booking_group_id`, so a retry job will eventually reconcile.
- The cancellation policy numbers (24h / 2h / 100% / 50%) are defined as config constants `REFUND_FULL_HOURS=24`, `REFUND_PARTIAL_HOURS=2`, `REFUND_PARTIAL_PCT=0.5`.

**Data touched:** `bookings` (select_for_update + update), `notifications` (insert), Payment Gateway call.

---

### 6.12 FR-12 · Apply Cancellation Policy Rules

| Attribute | Value |
|---|---|
| Use Case | UC-04 |
| Priority | MUST |
| Test Case | TC-12 |
| No separate endpoint — implemented inside FR-11 |

Policy is encoded in `BookingService.get_refund_policy(showtime_start, now) -> RefundPolicy` and is unit-testable in isolation. See §6.11 table for the rules.

**Also surfaced on the booking details response (FR-10)** as `cancellable` and `cancellationRefundEligible` so the UI can hide/disable the "Cancel" button.

---

### 6.13 FR-13 · Update User Profile Information

| Attribute | Value |
|---|---|
| Use Case | UC-05 |
| Priority | MUST |
| Test Case | TC-13 |
| APIs | `POST /api/users/register`, `POST /api/users/login`, `GET /api/users/{userId}`, `PUT /api/users/{userId}` |
| Auth | `AllowAny` for register/login; `IsOwnerOrAdmin` for read/update |

#### 6.13.1 `POST /api/users/register`

**Request:**
```json
{
  "firstName": "Mais",
  "lastName": "Al-Ahmad",
  "email": "mais@example.com",
  "password": "SecurePass!2026",
  "phone": "+962791234567",
  "preferredGenres": ["Action","Drama","Sci-Fi"]
}
```

**Rules:**
- `email` unique, lowercase, valid RFC 5322.
- `password` min 8 chars, at least 1 digit, 1 letter. (Django's `AUTH_PASSWORD_VALIDATORS` handles this.)
- `preferredGenres` optional; unknown genres silently dropped (or return 400 — choose strict-mode = **strict 400**: unknown genres return `GEN-400 Unknown genre: "XYZ"`).

**Flow:**
1. Validate with serializer.
2. If email exists → `AUTH-002 Email already registered` (409).
3. Hash password (PBKDF2).
4. Insert `users` row + `user_genre_preferences` rows in a single transaction.
5. Return user profile (no password hash).

**Response 201:** full user profile + no token. Client then calls `/login`.

#### 6.13.2 `POST /api/users/login`

**Request:** `{"email": "...", "password": "..."}`

**Flow:**
1. Load user by email.
2. If not found or `check_password` fails → `AUTH-001 Invalid credentials` (401). *Return the same error for both cases to prevent email enumeration.*
3. If `status='SUSPENDED'` → `AUTH-003 Account suspended` (403).
4. Issue JWT access + refresh.

**Response 200:**
```json
{"token": "...", "refreshToken": "...", "expiresIn": 3600, "userId": "..."}
```

#### 6.13.3 `GET /api/users/{userId}`

Returns full profile (name, email, phone, preferredGenres, createdAt). `IsOwnerOrAdmin`.

#### 6.13.4 `PUT /api/users/{userId}`

Updates any subset of `firstName, lastName, email, phone, password`. If password is updated:
- Require `currentPassword` in the request body.
- Increment `users.token_version` to invalidate old JWTs.

**Data touched:** `users`, `user_genre_preferences`.

---

### 6.14 FR-14 · Manage Saved Payment Methods

| Attribute | Value |
|---|---|
| Use Case | UC-05 |
| Priority | MUST |
| Test Case | TC-14 |
| API | `GET /api/users/{userId}/payment-methods`, `POST /api/users/{userId}/payment-methods`, `DELETE /api/users/{userId}/payment-methods/{methodId}` |

**CRITICAL: We never store PANs, CVVs, or expiry dates.** Per CINELUX-CONST-12, all sensitive data lives in the Payment Gateway. What we store is the **gateway's customer profile ID and the gateway's saved-card token**.

**Schema addition:**
```sql
CREATE TABLE saved_payment_methods (
    method_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    gateway_customer_id VARCHAR(128) NOT NULL,      -- opaque from gateway
    gateway_token    VARCHAR(128) NOT NULL,         -- opaque token to re-use
    brand            VARCHAR(20),                   -- 'VISA','MASTERCARD',...
    last4            CHAR(4) NOT NULL,              -- display only; not sensitive
    exp_month        INTEGER,                       -- display only
    exp_year         INTEGER,                       -- display only
    is_default       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_saved_pm_user ON saved_payment_methods (user_id);
```

**Rules:**
- `brand`, `last4`, `exp_month`, `exp_year` are **display-only data** returned by the gateway at tokenisation time. Storing them is not in PCI scope (no PAN).
- Admin cannot read this table via any endpoint (CINELUX-CONST-12).

**Flows:**

- **List** — returns array of `{methodId, brand, last4, expMonth, expYear, isDefault}`. No gateway tokens exposed.
- **Add** — React tokenises card with gateway SDK → POSTs `{gatewayCustomerId, gatewayToken, brand, last4, expMonth, expYear}`. We validate and store.
- **Delete** — calls gateway's "delete saved card" API AND removes our row. If gateway delete fails, we still remove our row (best-effort) and log.

---

### 6.15 FR-15 · Scan & Validate QR Code Ticket

| Attribute | Value |
|---|---|
| Use Case | UC-06 |
| Priority | MUST |
| Test Case | TC-15 |
| API | `POST /api/validate` |
| Auth | `IsStaffOrAdmin` |

**Request:**
```json
{
  "qrToken": "QR-grp_x1y2z3-2026041419300"
}
```

**Response 200 (valid):**
```json
{
  "result": "VALID",
  "bookingGroupId": "grp_x1y2z3",
  "movieTitle": "Dune: Part Three",
  "showtime": "2026-04-20T19:30:00Z",
  "hall": "Hall 3",
  "seats": ["A1","A2"],
  "userName": "Mais A."
}
```

**Response 400 (invalid):**
```json
{ "result": "INVALID", "errorCode": "VAL-401", "message": "Ticket not found" }
```

**Response 409 (already used):**
```json
{ "result": "ALREADY_USED", "errorCode": "VAL-409", "usedAt": "2026-04-20T19:28:00Z" }
```

**Flow (`ValidationService.validate`):**

1. Look up bookings by `qr_token`. If none → `VAL-401`.
2. Load `showtime`. Rules:
   - If `booking.status = 'USED'` → `VAL-409`, return `used_at`.
   - If `booking.status = 'CANCELLED'` → `VAL-403` "Ticket cancelled".
   - If `booking.status != 'CONFIRMED'` → `VAL-400`.
   - If `NOW() < showtime.start_time - 30 minutes` → `VAL-410 Too early` (configurable).
   - If `NOW() > showtime.end_time` → `VAL-411 Show ended`.
3. Mark **all rows in the booking group** as `USED` with `used_at = NOW()` (atomic). See FR-16 for the exact side effects.
4. Return the valid response.

**Data touched:** `bookings` (read + update), FR-16 entry log.

---

### 6.16 FR-16 · Mark Ticket as Used & Log Entry

| Attribute | Value |
|---|---|
| Use Case | UC-06 |
| Priority | MUST |
| Test Case | TC-16 |
| No separate endpoint — executed inside FR-15's `validate` |

**Schema addition:**
```sql
CREATE TABLE entry_logs (
    entry_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_group_id UUID NOT NULL,
    validator_user_id UUID NOT NULL REFERENCES users(user_id),
    showtime_id     UUID NOT NULL REFERENCES showtimes(showtime_id),
    result          VARCHAR(20) NOT NULL,  -- 'VALID','ALREADY_USED','INVALID'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_entry_logs_showtime ON entry_logs (showtime_id);
```

**Flow (inside the same transaction as FR-15 step 3):**

1. Update `bookings` where `booking_group_id=X`: `status='USED'`, `used_at=NOW()`.
2. Insert one `entry_logs` row with `result='VALID'` and the validator's user_id (from JWT).
3. For `INVALID`/`ALREADY_USED` responses, **still** insert an `entry_logs` row with that result — for forensic analysis.

**Data touched:** `bookings`, `entry_logs`.

---

### 6.17 FR-17 · Add & Update Movies and Showtimes

| Attribute | Value |
|---|---|
| Use Case | UC-07 |
| Priority | MUST |
| Test Case | TC-17 |
| APIs | `POST /api/admin/movies`, `PUT /api/admin/movies/{movieId}`, `DELETE /api/admin/movies/{movieId}`, `POST /api/admin/showtimes`, `PUT /api/admin/showtimes/{showtimeId}`, `DELETE /api/admin/showtimes/{showtimeId}` |
| Auth | `IsAdmin` |

**Add Movie** `POST /api/admin/movies`

**Request:**
```json
{
  "title": "Oppenheimer II",
  "description": "The aftermath of Trinity...",
  "durationMinutes": 140,
  "releaseDate": "2027-07-21",
  "language": "English",
  "ageRating": "PG-13",
  "posterUrl": "https://cdn.cinema.io/posters/op2.jpg",
  "genres": ["Drama","History"],
  "metadata": {
    "cast": ["Cillian Murphy"],
    "keywords": ["bomb","Cold War"],
    "tags": ["biopic","historic"]
  }
}
```

**Flow:**
1. Validate body.
2. Insert `movies` row.
3. Resolve genre names to genre_ids; insert `movie_genres` (create unknown genres or reject? **Reject with `GEN-400`** — curate the genre list).
4. Insert an `admin_actions` audit row.
5. Return the created movie.

**Update Movie** `PUT /api/admin/movies/{movieId}` — partial update (PATCH semantics, but convention says PUT per Task 4 doc). All fields optional.

**Delete Movie** `DELETE /api/admin/movies/{movieId}` — **soft delete**:
- Set `movies.is_active = false`.
- Deactivate all future showtimes: `UPDATE showtimes SET is_active=false WHERE movie_id=:id AND start_time > NOW()`.
- **Existing CONFIRMED bookings are untouched.** They still show in the user's history and can still be validated at the gate.
- Insert `admin_actions` row.

**Add Showtime** `POST /api/admin/showtimes`

**Request:**
```json
{
  "movieId": "mov_abc123",
  "hallId": "hal_03",
  "startTime": "2026-05-01T20:00:00Z",
  "price": 12.00,
  "currency": "USD"
}
```

**Flow:**
1. Load movie; compute `endTime = startTime + durationMinutes + 30min` (buffer for trailers/cleaning; configurable).
2. Insert `showtimes`. The `no_hall_overlap` exclusion constraint (§4.2) **automatically rejects overlapping showtimes** with a PostgreSQL `ExclusionConstraintViolation` — catch and return `SHOW-409 Schedule conflict`. This maps to **TC-17 (from the slides)**: "System throws 'Schedule Overlap Error'".
3. Audit log.

**Update/Delete Showtime:** analogous; delete is **soft** (`is_active=false`), existing bookings untouched.

**Data touched:** `movies`, `movie_genres`, `showtimes`, `admin_actions`.

---

### 6.18 FR-18 · Manage Screening Rooms & Seat Maps

| Attribute | Value |
|---|---|
| Use Case | UC-07 |
| Priority | MUST |
| Test Case | TC-18 |
| APIs | `POST /api/admin/halls`, `PUT /api/admin/halls/{hallId}`, `GET /api/admin/halls`, `POST /api/admin/halls/{hallId}/seats` (bulk seat generation) |
| Auth | `IsAdmin` |

**Seat-map generation helper** `POST /api/admin/halls/{hallId}/seats`:

Rather than submitting 100 seat rows individually, admins submit a seat-map spec:
```json
{
  "rows": [
    { "label": "A", "seatCount": 10, "type": "STANDARD" },
    { "label": "B", "seatCount": 10, "type": "STANDARD" },
    { "label": "C", "seatCount": 8,  "type": "PREMIUM" }
  ]
}
```

**Flow:**
1. Load hall; fail if it already has seats (`CONFLICT` — seat map is immutable once bookings exist; **new deployment requires a new hall**).
2. Bulk insert via `Seat.objects.bulk_create(...)`.
3. Update `halls.total_seats`.

**Why immutable once bookings exist?** Re-numbering seats after tickets have been issued breaks QR validation. Keep it simple: new seat layout = new hall record + migrate future showtimes.

---

### 6.19 FR-19 · Create & Suspend User Accounts

| Attribute | Value |
|---|---|
| Use Case | UC-08 |
| Priority | MUST |
| Test Case | TC-19 |
| APIs | `POST /api/admin/users`, `PATCH /api/admin/users/{userId}`, `GET /api/admin/users`, `GET /api/admin/users/{userId}` |
| Auth | `IsAdmin` |

**Create user** (`POST /api/admin/users`): same as self-register (FR-13.1) but admin can set `role` directly.

**Patch user** (`PATCH /api/admin/users/{userId}`): optional fields:
- `status`: `'ACTIVE'` or `'SUSPENDED'`
- `role`: `'USER'`, `'ADMIN'`, or `'STAFF'`

Suspension side-effect: increment `users.token_version` → next request with an old JWT fails auth → user is effectively logged out. Login attempts return `AUTH-003`.

**List users** (`GET /api/admin/users`): paginated, filterable by role and status. Exposes `email, name, role, status, createdAt, lastLoginAt` — **never** password hash, token version, or payment methods.

---

### 6.20 FR-20 · Assign Roles & Manage Permissions

| Attribute | Value |
|---|---|
| Use Case | UC-08 |
| Priority | MUST |
| Test Case | TC-20 |
| API | `PATCH /api/admin/users/{userId}` (role field) |
| Auth | `IsAdmin` |

Role is a single string column (see §4.2 `users.role`). No hierarchy, no inheritance. Permission checks read the role directly from the JWT claim.

**Rules:**
- An admin cannot demote themselves if they are the last remaining ADMIN. The service checks `SELECT COUNT(*) FROM users WHERE role='ADMIN' AND status='ACTIVE'` and refuses with `ADM-409 Cannot demote last admin`.
- Role changes invalidate old JWTs (same `token_version` trick).

**Data touched:** `users`, `admin_actions`.

---

*(Non-functional requirements, externals, error model, project structure continue in next section)*

---

## 7. Non-Functional Requirements

Sourced from the SRS (slide 2). Cross-referenced with FRs that are most affected.

| NFR ID | Type | Priority | Requirement | Implementation |
|---|---|---|---|---|
| NFR-01 | Performance | MUST | Search queries respond in < 2.0 s under peak load | pg_trgm index on `movies.title`; composite indexes on `showtimes(movie_id,start_time)`; DRF pagination defaults to 20/page. Measure with Django Silk or p95 logging. |
| NFR-02 | Security | MUST | Passwords hashed with BCrypt; data encrypted via SSL/TLS | Django PBKDF2 default is acceptable (see §12.2); enable HTTPS via nginx + Let's Encrypt/self-signed in academic deployment; enforce HSTS. |
| NFR-03 | Usability | SHOULD | Responsive on mobile, tablet, desktop | React + Tailwind responsive breakpoints; manual QA on three viewport sizes before each release. |
| NFR-04 | Reliability | MUST | 99.9% uptime excl. scheduled maintenance | Single-VM constraint caps realistic uptime at ~99.5%. Define "excl. scheduled maintenance" windows in the deployment doc. Monitor with `systemctl` + a simple nagios/cron ping. |
| NFR-05 | Maintainability | SHOULD | Modular architecture for easy updates | **NOTE:** The SRS slide says "microservices" but CINELUX-CONST-05 explicitly forbids them. **Interpretation:** modular monolith with clear layer boundaries (§2.4) satisfies the intent. Document this reconciliation. |
| NFR-06 | Compatibility | MUST | Works in Chrome, Safari, Edge | React 18 + modern browserslist; no IE. Smoke test on latest stable of each. |
| NFR-07 | Security | MUST | Payment module PCI-DSS compliant | We are **outside PCI scope** because no PAN/CVV ever touches our servers. All card data is tokenised client-side by the Payment Gateway SDK. Document this as "PCI-DSS SAQ-A eligible". |
| NFR-08 | Performance | MUST | 5,000 concurrent active users | Single VM unlikely to meet this literally. Gunicorn with ≥ (2 × CPU_CORES + 1) workers; pgbouncer in front of PostgreSQL (if available); the `availableSeats` counter optimisation (§6.3.2) if needed. **Escalate to sponsor if real load-testing reveals VM cannot cope** — this is the most at-risk NFR given the hardware constraint. |

---

## 8. External Integrations

Per CINELUX-CONST-11, every external call:
- runs with a **5–10 s timeout**,
- has a documented **fallback**,
- is **wrapped in try/except** so external failure never crashes the parent flow.

### 8.1 Payment Gateway

**Interface:** a thin Python adapter `cinelux.externals.payment_gateway.PaymentGateway`.

**Methods:**
```python
class PaymentGateway:
    def charge(self, token: str, amount: Decimal, currency: str,
               idempotency_key: str) -> ChargeResult: ...
    def refund(self, transaction_id: str, amount: Decimal,
               idempotency_key: str) -> RefundResult: ...

class ChargeResult:
    status: Literal['SUCCESS','DECLINED','ERROR']
    transaction_id: str | None
    decline_reason: str | None          # e.g. 'INSUFFICIENT_FUNDS'
    raw: dict                           # raw gateway response for audit
```

**Config:** `PAYMENT_GATEWAY_URL`, `PAYMENT_GATEWAY_API_KEY` (env).

**Simulated implementation (MVP):** no real network calls. Matches token prefixes:
- `tok_good_*` → SUCCESS with a fake `transaction_id = "PAY-SIM-{uuid}"`.
- `tok_bad_*` → DECLINED, reason `CARD_DECLINED`.
- `tok_slow_*` → sleep 12s → raises timeout → ERROR.
- `tok_network_*` → raises `ConnectionError` → ERROR.

**Fallback:**
- On `ERROR` during `charge()`: do NOT confirm the booking; return `PAY-503` to the client. Seats stay PENDING; they expire in 10 min.
- On `ERROR` during `refund()`: mark the booking CANCELLED (seats released) and push the refund onto a retry queue (implemented as a row in a new `pending_refunds` table, swept by APScheduler).

### 8.2 Notification Service

**Interface:**
```python
class NotificationService:
    def send_email(self, to: str, subject: str, body: str,
                   attachments: list[Attachment] | None = None) -> SendResult: ...
    def send_sms(self, to: str, body: str) -> SendResult: ...
```

**Config:** `NOTIFICATION_SERVICE_URL`, `NOTIFICATION_SERVICE_API_KEY` (env). For MVP, a stub that writes to `/var/log/cinelux/notifications.log` and returns SUCCESS is acceptable.

**Flow:**
- Every outbound notification **creates a `notifications` row first** with `status='PENDING'`.
- Then calls the service. On success → `status='SENT'`, `sent_at=NOW()`. On failure → `status='FAILED'`, `retry_count += 1`.
- **APScheduler** retries FAILED rows every 5 min, up to 3 times. After that, status stays FAILED and is flagged in the admin dashboard.

**Fallback:** notification failure **never** rolls back the transaction that caused it. The user's booking is already confirmed on DB commit; the email is a best-effort side effect. UI shows "A confirmation email is on its way" — we commit before we attempt, and the retry loop eventually delivers.

### 8.3 AI Recommendation Engine

Per the architecture diagrams, the recommendation engine is an **internal component** (a Python service, not an external HTTP call). No external API. It runs in-process with scikit-learn. See §6.4 for the algorithm.

---

## 9. Unified Error Model

### 9.1 Response shape

Every error returns HTTP status + JSON:
```json
{
  "errorCode": "SEAT-409",
  "message": "Seat already booked.",
  "details": "Seat A12 is unavailable for showtime sho_001",
  "traceId": "req_abc123"
}
```

`traceId` is set from the middleware (`X-Request-ID` header); it lets support trace a user-reported error to server logs.

### 9.2 Error code catalogue

| Code | HTTP | Meaning |
|---|---|---|
| GEN-400 | 400 | Validation error — malformed body / unknown genre / bad param |
| GEN-401 | 401 | Missing or invalid JWT |
| GEN-403 | 403 | Authenticated but not authorised |
| GEN-404 | 404 | Generic resource not found |
| GEN-500 | 500 | Unhandled server error |
| AUTH-001 | 401 | Invalid credentials (email/password mismatch — same error for unknown email) |
| AUTH-002 | 409 | Email already registered |
| AUTH-003 | 403 | Account suspended |
| MOV-404 | 404 | Movie not found or inactive |
| SHOW-404 | 404 | Showtime not found |
| SHOW-409 | 409 | Showtime schedule conflict (hall overlap) |
| SEAT-404 | 404 | Seat not found |
| SEAT-409 | 409 | Seat already booked or held |
| BOOK-404 | 404 | Booking not found |
| BOOK-403 | 403 | Cancellation not allowed (outside window or already used) |
| BOOK-410 | 410 | Seat hold expired |
| BOOK-422 | 422 | Showtime already started — cannot book |
| PAY-402 | 402 | Payment declined by gateway |
| PAY-503 | 503 | Payment gateway unavailable |
| VAL-400 | 400 | Ticket not in CONFIRMED state |
| VAL-401 | 400 | Ticket not found |
| VAL-403 | 403 | Ticket cancelled |
| VAL-409 | 409 | Ticket already used |
| VAL-410 | 425 | Too early — show has not started yet (entry opens X min before) |
| VAL-411 | 410 | Show has already ended |
| REC-500 | 500 | Recommendation engine failure (client still receives fallback list with HTTP 200; REC-500 is for internal logs only) |
| ADM-409 | 409 | Admin-side conflict (e.g. cannot demote last admin) |

### 9.3 Error handling policy

- **Never leak stack traces** to the client in production.
- `GEN-500` responses must log full traceback + traceId server-side.
- Rate limit repeated `AUTH-001` by IP (10 attempts / 15 min) — Django's `django-ratelimit` package.

---

## 10. Project Structure & Implementation Plan

### 10.1 Repository layout

```
cinelux/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── cinelux/                # Django project
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── dev.py
│   │   │   └── prod.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── users/              # UserAPI, UserService, UserRepo, models
│   │   │   ├── api.py          # DRF ViewSets / APIViews
│   │   │   ├── serializers.py
│   │   │   ├── services.py
│   │   │   ├── repository.py
│   │   │   ├── models.py
│   │   │   ├── permissions.py
│   │   │   └── tests/
│   │   ├── catalogue/          # Movies, Showtimes, Halls, Seats
│   │   ├── bookings/           # Booking, Hold, Confirm, Cancel
│   │   ├── recommendations/
│   │   ├── validation/         # Gate staff QR scan
│   │   ├── admin_panel/        # Admin APIs (distinct from Django admin)
│   │   └── notifications/
│   ├── externals/
│   │   ├── payment_gateway.py  # adapter
│   │   └── notification_service.py
│   ├── scheduler/              # APScheduler jobs
│   │   └── jobs.py
│   └── common/
│       ├── exceptions.py       # custom exception → error code mapping
│       ├── middleware.py       # trace ID, request logging
│       └── pagination.py
├── frontend/                   # React SPA (Vite)
│   ├── package.json
│   ├── src/
│   │   ├── pages/              # BrowseMovies, MovieDetails, SeatPicker, Bookings, Admin...
│   │   ├── components/
│   │   ├── api/                # thin axios wrappers per API group
│   │   ├── hooks/
│   │   ├── store/              # auth token, user profile
│   │   └── routes.tsx
│   └── vite.config.ts
├── deploy/
│   ├── nginx.conf
│   ├── gunicorn.service        # systemd unit
│   └── migrate.sh
└── docs/
    ├── PRD.md                  # this document
    ├── ERD.png
    └── architecture.png
```

### 10.2 Recommended implementation order

**Phase 0 — Foundations (Week 1)**
1. Initialise Django project, PostgreSQL, Docker-free local dev environment.
2. Create migrations for §4.2 schema (commit the SQL above as a Django migration).
3. Load seed genres + one admin user + one hall with a 100-seat map.
4. Wire up JWT auth (FR-13.1, FR-13.2).
5. Implement `common/exceptions.py` and the unified error middleware.

**Phase 1 — Core booking path (Weeks 2–4)**
6. FR-01, FR-02, FR-03 — catalogue browse + details.
7. FR-06 seat map + hold.
8. FR-07 confirm (with stubbed Payment Gateway).
9. FR-08 QR generation + notifications stub.
10. FR-09, FR-10 — booking history and details.
11. FR-11, FR-12 — cancellation with policy.

**Phase 2 — User features (Week 5)**
12. FR-13 full profile CRUD.
13. FR-14 saved payment methods.
14. FR-04, FR-05 — recommendations + trending.

**Phase 3 — Gate and Admin (Week 6)**
15. FR-15, FR-16 — validation + entry log.
16. FR-17, FR-18 — admin movie/showtime/hall CRUD.
17. FR-19, FR-20 — admin user management.

**Phase 4 — Hardening (Weeks 7–8)**
18. APScheduler jobs (booking expiry, notification retries, similarity refresh).
19. Rate limiting, HTTPS, HSTS, admin audit log.
20. End-to-end tests (TC-01…TC-20).
21. Performance pass: `EXPLAIN ANALYZE` on hot queries; add indexes as needed.
22. Deployment to the university VM via gunicorn + nginx.

### 10.3 Testing

- **Unit tests** (pytest-django) — one test file per service class. Cover all rules in §6. Target ≥ 80% on service layer.
- **Integration tests** — one per TC-XX (see §6). Spin up a test DB, exercise the HTTP endpoint, assert response + DB state.
- **Concurrency test** (critical) — two threads calling `/bookings/hold` for the same seat; assert one gets 201 and one gets SEAT-409. Use `threading` with a shared test DB.
- **Load test** (deferred to Phase 4) — Locust or k6 script targeting FR-01 and FR-06 (seat map). 100 concurrent users on the VM; capture p95.

### 10.4 Configuration (environment variables)

All listed in `backend/cinelux/settings/base.py` with sensible dev defaults:

| Var | Example | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgres://cinelux:pw@localhost/cinelux` | Postgres DSN |
| `DJANGO_SECRET_KEY` | 64-char random | signing |
| `JWT_ACCESS_LIFETIME_MIN` | `60` | access token TTL |
| `JWT_REFRESH_LIFETIME_DAYS` | `7` | refresh token TTL |
| `BOOKING_HOLD_MINUTES` | `10` | seat hold window |
| `REFUND_FULL_HOURS` | `24` | full refund threshold |
| `REFUND_PARTIAL_HOURS` | `2` | partial refund threshold |
| `REFUND_PARTIAL_PCT` | `0.5` | partial refund % |
| `PAYMENT_GATEWAY_URL` | `...` | PG endpoint |
| `PAYMENT_GATEWAY_API_KEY` | `...` | PG auth |
| `NOTIFICATION_SERVICE_URL` | `...` | NS endpoint |
| `NOTIFICATION_SERVICE_API_KEY` | `...` | NS auth |
| `CINELUX_ADMIN_EMAIL` | `admin@cinelux.local` | bootstrap admin |
| `CINELUX_ADMIN_PASSWORD` | `...` | bootstrap admin |
| `CINEMA_TIMEZONE` | `Asia/Amman` | local TZ for date filters |
| `PUBLIC_BASE_URL` | `https://cinelux.example.com` | used in QR URLs and emails |
| `CORS_ALLOWED_ORIGINS` | `https://cinelux.example.com` | React app origin |

---

## 11. Acceptance Criteria

The system is "done" when:

1. **All 20 functional requirements** are implemented per §6, with each TC-XX from the RTM passing (automated test + manual demo).
2. **All 8 NFRs** are documented as met, with evidence:
   - NFR-01: query timings logged + summary < 2s p95.
   - NFR-02: PBKDF2 configured; HTTPS enabled; test with SSL Labs → A+ (or best-effort on academic domain).
   - NFR-03: manual responsive QA signoff.
   - NFR-04: uptime monitoring doc.
   - NFR-05: architecture diagram + layer rules enforced.
   - NFR-06: browser smoke-test matrix.
   - NFR-07: written PCI scope analysis.
   - NFR-08: load-test report.
3. **End-to-end smoke test** runs cleanly:
   - Admin creates a movie + showtime.
   - User registers → logs in → browses → receives recommendation → books 2 seats → pays → receives email (log file) with QR.
   - User cancels within refund window → receives refund email.
   - Gate staff scans QR → marked USED → second scan returns ALREADY_USED.
4. **Security review** — OWASP Top-10 cross-check documented, rate limits on auth endpoints active, no raw card data in any log/DB.
5. **Deployed to the university VM** and accessible over HTTPS.
6. **Documentation** — this PRD + a 2-page ops runbook (deploy/rollback/restore-backup procedures).

---

## 12. Open Questions Resolved

The source documents contained several ambiguities. This section records the decisions made so the implementation agent doesn't need to re-ask.

### 12.1 Identifier type — UUID vs INT

**Question:** The ERD uses `INT` primary keys; the API docs use string IDs like `usr_9f4a2b1c`.

**Decision:** **UUIDv4** (PostgreSQL `UUID` type, `gen_random_uuid()`).

**Why:**
- URL-safe (can't enumerate users by ID).
- Stateless (no auto-increment coordination across any future replica).
- Django's `UUIDField` is trivial to use.
- Storage overhead (16 vs 4 bytes) is irrelevant at MVP scale.

The "usr_" / "mov_" / "bkg_" prefixes in the API docs are **purely cosmetic** in the examples. Our real IDs are canonical UUIDv4 strings (`9f4a2b1c-6e5d-...`). The API accepts and returns them as bare strings.

### 12.2 Password hashing — BCrypt vs PBKDF2

**Question:** NFR-02 specifies BCrypt; Django's default is PBKDF2.

**Decision:** **Use Django's default PBKDF2-SHA256 with the 2024+ iteration count (600k).** It meets the spirit of NFR-02 (industry-standard slow hash with salt). If the sponsor insists on BCrypt specifically, add `django[bcrypt]` to requirements and set `PASSWORD_HASHERS` with `BCryptSHA256PasswordHasher` first.

### 12.3 Pricing model

**Question:** The class diagram shows `ShowtimePricing` with per-seat-type pricing; the MVP API shows a flat `price` per showtime.

**Decision:** **Flat price per showtime** for MVP. The `Showtime.price` column is the single price paid by any seat type. Per-seat-type pricing is deferred post-MVP.

### 12.4 Booking row cardinality

**Question:** One booking row per seat? Or one booking row per purchase with a join table of seats?

**Decision:** **One row per seat** (see §4.2 `bookings` table), grouped by `booking_group_id`. Justification:
- The ERD has a `seat_id` FK on the `Bookings` table (supports one-row-per-seat).
- Simpler query for concurrency (`SELECT … FOR UPDATE` on seat-level rows).
- The `uniq_active_seat_per_showtime` partial index gives an atomic, race-free "one-active-booking-per-seat" guarantee at the DB level.
- User-facing responses group by `booking_group_id` so the UI still shows one "ticket card" per purchase.

### 12.5 Recommendation algorithm — CBF only vs CF + CBF hybrid

**Question:** Task 4 doc describes a hybrid CF + CBF. Task 3 tech-stack doc also mentions it. The class diagram has `CollaborativeFiltering` and `ContentBasedFiltering` strategy classes.

**Decision:** **Ship CBF only in MVP.** The `IRecommendationStrategy` interface is retained (per the class diagram), with `ContentBasedFiltering` as the only implementation shipped. CF can be added later by plugging in a second strategy class.

**Why:**
- CF requires a dense user-user booking matrix that only becomes useful at >1000 users with >5 bookings each — we won't have that data at MVP launch.
- CBF alone solves cold-start, which is where a university demo spends most of its evaluation.
- Simpler = on-time delivery (CINELUX-CONST-01, -02).

### 12.6 "Microservices" in NFR-05 vs "No Microservices" in CINELUX-CONST-05

**Question:** Direct conflict between slide 2 NFR-05 and the constraints doc.

**Decision:** **Constraints override NFRs.** Build a modular monolith with strict layer boundaries (§2.4). Document in the NFR-05 section that we interpret "modular" as "cleanly decomposed modules with dependency rules", not "separately deployable services".

### 12.7 Customer vs End User vs Staff vs Gate Staff terminology

**Question:** Various docs use `Customer`, `End User`, `User`, interchangeably; `Staff` and `Gate Staff` too.

**Decision:** Canonical terms for this project:
- **Customer** = end-user who browses/books. DB `role = 'USER'`.
- **Gate Staff** = validates tickets. DB `role = 'STAFF'`.
- **Administrator** / **Admin** = catalogue + user management. DB `role = 'ADMIN'`.

### 12.8 FR numbering — SRS slide vs RTM

**Question:** The SRS slide 1 lists FRs differently from the RTM:
- SRS slide: FR-04=AI Recs, FR-05=Seat Map, FR-06=Multi-ticket types, FR-07=Snacks, FR-08=Payment, etc.
- RTM (and this PRD): FR-04=Personalised Recs, FR-05=Trending, FR-06=Select Seats, FR-07=Payment, FR-08=E-ticket, etc.

**Decision:** **This PRD's numbering (which matches the RTM in `cinelux_system_rtm.pdf`) is canonical.** The SRS slide is from an earlier draft. Multi-ticket-type pricing and snacks are out of MVP scope and not in the RTM; align all documentation to the RTM numbering.

### 12.9 Entry log table

**Question:** The RTM mentions "Mark Ticket as Used & Log Entry" (FR-16) but no log table is shown in the ERD.

**Decision:** Introduced `entry_logs` (§6.16). Necessary for audit and required to distinguish FR-15 (validate) from FR-16 (log), otherwise FR-16 has no write-side behaviour.

### 12.10 Saved payment methods

**Question:** FR-14 says "Manage saved payment methods" but no ERD table exists.

**Decision:** Introduced `saved_payment_methods` (§6.14) storing only gateway tokens + display data (brand, last4). No PAN, no CVV — stays out of PCI scope.

### 12.11 Showtime end_time — stored or computed

**Question:** ERD doesn't show `end_time` on `showtimes`.

**Decision:** **Store it** (§4.2) and compute on insert as `start_time + duration + 30min buffer`. Enables:
- Hall overlap exclusion constraint (§4.2).
- O(1) query for "is the show still running" in FR-15.

### 12.12 JWT invalidation on password change / role change

**Question:** Not specified in source docs.

**Decision:** Use a `users.token_version` integer column and a custom JWT authentication class that verifies `token.version == user.token_version`. Bump on password change, suspension, and role change. See §5.4.

---

## 13. Appendix

### 13.1 Quick endpoint index

| FR | Method | Path | Service | Auth |
|---|---|---|---|---|
| 01, 02 | GET | `/api/movies` | CatalogueService.browse | AllowAny |
| 03 | GET | `/api/movies/{id}` | CatalogueService.getDetails | AllowAny |
| 03 | GET | `/api/movies/{id}/showtimes` | CatalogueService.getShowtimes | AllowAny |
| 04 | GET | `/api/recommendations/{userId}` | RecommendationService.recommend | IsOwnerOrAdmin |
| 05 | GET | `/api/movies/trending` | CatalogueService.trending | AllowAny |
| 06 | GET | `/api/showtimes/{id}/seats` | BookingService.getSeatMap | IsAuthenticated |
| 06 | POST | `/api/bookings/hold` | BookingService.holdSeats | IsAuthenticated |
| 07, 08 | POST | `/api/bookings/confirm` | BookingService.confirm | IsAuthenticated |
| 09 | GET | `/api/bookings?userId=...` | BookingService.listForUser | IsOwnerOrAdmin |
| 10 | GET | `/api/bookings/{id}` | BookingService.get | IsOwnerOrAdmin |
| 11, 12 | DELETE | `/api/bookings/{id}` | BookingService.cancel | IsOwnerOrAdmin |
| 13 | POST | `/api/users/register` | UserService.register | AllowAny |
| 13 | POST | `/api/users/login` | UserService.login | AllowAny |
| 13 | GET | `/api/users/{id}` | UserService.get | IsOwnerOrAdmin |
| 13 | PUT | `/api/users/{id}` | UserService.update | IsOwnerOrAdmin |
| 13 | PUT | `/api/users/{id}/preferences` | UserService.updatePreferences | IsOwnerOrAdmin |
| 14 | GET | `/api/users/{id}/payment-methods` | UserService.listPM | IsOwnerOrAdmin |
| 14 | POST | `/api/users/{id}/payment-methods` | UserService.addPM | IsOwnerOrAdmin |
| 14 | DELETE | `/api/users/{id}/payment-methods/{mid}` | UserService.deletePM | IsOwnerOrAdmin |
| 15, 16 | POST | `/api/validate` | ValidationService.validate | IsStaffOrAdmin |
| 17 | POST | `/api/admin/movies` | AdminService.createMovie | IsAdmin |
| 17 | PUT | `/api/admin/movies/{id}` | AdminService.updateMovie | IsAdmin |
| 17 | DELETE | `/api/admin/movies/{id}` | AdminService.deleteMovie | IsAdmin |
| 17 | POST | `/api/admin/showtimes` | AdminService.createShowtime | IsAdmin |
| 17 | PUT | `/api/admin/showtimes/{id}` | AdminService.updateShowtime | IsAdmin |
| 17 | DELETE | `/api/admin/showtimes/{id}` | AdminService.deleteShowtime | IsAdmin |
| 18 | POST | `/api/admin/halls` | AdminService.createHall | IsAdmin |
| 18 | POST | `/api/admin/halls/{id}/seats` | AdminService.createSeatMap | IsAdmin |
| 19, 20 | POST | `/api/admin/users` | AdminService.createUser | IsAdmin |
| 19, 20 | PATCH | `/api/admin/users/{id}` | AdminService.patchUser | IsAdmin |
| 19 | GET | `/api/admin/users` | AdminService.listUsers | IsAdmin |

### 13.2 RTM cross-reference

All 20 FRs map to TC-01 … TC-20 exactly (see RTM section in `cinelux_system_rtm.pdf`). Detailed Design entries (DD-01…DD-20) correspond 1:1 to the "Flow" subsections of each FR in §6. Coding and UI columns are satisfied by the implementation plan in §10.2.

### 13.3 Glossary

| Term | Meaning |
|---|---|
| Booking group | A set of `bookings` rows sharing `booking_group_id`, representing one purchase of N seats. |
| Hold | Temporary reservation of seats with `status=PENDING` and an expiry time; frees up if not confirmed. |
| QR token | Opaque string stored in `bookings.qr_token`; encoded into the QR image; looked up on scan. |
| Cold-start | A user with no booking history and no ratings; served popularity-based recommendations instead of CBF. |
| Trace ID | UUID set on each inbound request and propagated to logs and error responses. |
| Refund policy | The rule table in §6.11 mapping `hours until showtime` to `refund %`. |

---

**End of PRD.**