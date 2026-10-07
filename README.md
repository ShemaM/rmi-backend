# RMI Backend

REST API for the **Regional Migration Intelligence (RMI)** platform: a hub connecting researchers, policymakers, institutions and practitioners across East Africa, the Great Lakes and Southern Africa with migration research, data, funding opportunities and expert networks.

This repository is the Django + Django REST Framework backend. The Next.js frontend lives in a separate repository.

| | |
|---|---|
| **Status** | Sprint 0 — foundation (90-day Phase 1 build) |
| **Backend lead** | Nzabakamira Shema Manasseh |
| **Frontend lead** | Emma |
| **Spec** | *RMI Platform Strategy & Feature Roadmap v1.0* (24 Aug 2026) |

---

## Contents

- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Core design rules](#core-design-rules)
- [Getting started](#getting-started)
- [Environment variables](#environment-variables)
- [Everyday commands](#everyday-commands)
- [API conventions](#api-conventions)
- [Testing](#testing)
- [Contributing workflow](#contributing-workflow)
- [Roadmap](#roadmap)

---

## Tech stack

| Concern | Choice |
|---|---|
| Language / framework | Python 3.12, Django 5.2 LTS, Django REST Framework |
| Database | PostgreSQL 16 (full-text search + trigram for typo-tolerant search) |
| Cache / broker | Redis 7 |
| Background jobs | Celery + Celery Beat (digests, imports, expiry, reminders) |
| API docs | drf-spectacular (OpenAPI 3, Swagger UI, Redoc) |
| Audit history | django-simple-history |
| Password hashing | Argon2 |
| Payments | Paystack / Flutterwave *(Sprint 4)* |
| File storage | Private S3-compatible bucket + signed download grants *(Sprint 2)* |
| Quality | pytest, factory_boy, Ruff, pre-commit, GitHub Actions |

## Architecture

A **modular monolith**: one Django project, one database, one domain per app under `apps/`. Apps map directly to the functional areas in the spec.

| App | Domain | Phase | Status |
|---|---|---|---|
| `core` | Shared base models, pagination, error envelope, health check | 1 | ✅ Scaffolded |
| `accounts` | Users, auth, profiles, email verification, staff roles | 1 | 🟡 User model only |
| `organizations` | Institutional profiles, seats, invitations, org admins | 1 | 🟡 Foundation |
| `billing` | Plans, entitlements, subscriptions, payments, invoices | 1 | ⬜ |
| `taxonomy` | Countries, regions, themes, multilingual tags | 1 | ⬜ |
| `library` | Publications, attachments, datasets, download grants | 1 | ⬜ |
| `opportunities` | Grants, tenders, fellowships, submissions, saved searches, digests | 1 | ⬜ |
| `observatory` | Indicators, data points, country profiles, situation reports | 1 | ⬜ |
| `cms` | Pages, posts, menus, banners, newsletter, partner intake | 1 | ⬜ |
| `policy` | Legislation directory, policy tracker, comparisons | 2 | ⬜ |
| `directory` | Expert profiles, verification, matchmaking | 2 | ⬜ |
| `alerts` | Early-warning bulletins | 3 | ⬜ |
| `academy` | Courses, modules, enrollments, certificates | 3 | ⬜ |
| `engagements` | Consultancy requests, leads, proposals | 3 | ⬜ |

```
rmi-backend/
├── apps/
│   ├── core/            # TimeStampedModel, SoftDeleteModel, error handler, /health
│   └── accounts/        # Custom User (UUID pk, email login)
├── config/
│   ├── settings/        # base.py, dev.py, test.py, prod.py
│   ├── celery.py
│   └── urls.py          # /api/v1/, /api/docs/, /admin/
├── docs/
│   └── DECISIONS.md     # architecture decision log
├── requirements/        # base.txt, dev.txt, prod.txt
├── .github/workflows/   # CI
├── conftest.py          # shared pytest fixtures
├── docker-compose.yml   # Postgres, Redis, Mailpit for local dev
├── Dockerfile           # production image (gunicorn)
└── Makefile
```

## Core design rules

These come straight from the spec and apply to every app. Reviewers should reject PRs that break them.

1. **Three-tier access on every content resource (D3).** Each gated model has `access_tier ∈ {public, registered, paid}`. Serializers check the caller's entitlements; if access is missing they withhold the body and file URLs and return `locked: true` plus the `unlock_plan`, so the frontend can show a paywall.
2. **Files are never public (D4).** Uploads live in private storage. Downloads go through a `DownloadGrant`: short-lived (5 min), single-use, audited, issued only after the entitlement check.
3. **History on editorial models (D5).** Everything inherits `core.TimeStampedModel`. Publications, policy tools, opportunities and indicators also get `HistoricalRecords()`.
4. **Archive, never delete (D6).** Editorial models inherit `core.SoftDeleteModel`; `.delete()` sets `archived_at`. Use `hard_delete()` only in data-fix scripts.
5. **Entitlements, not job titles.** Access to paid content is decided by what a user's plan (personal or via their organization) grants, never by checking `is_staff` or a role name.
6. **Aggregate data only.** The platform never stores personally identifiable data about refugees or displaced people. Datasets need an analyst's aggregation sign-off before release (FR-LIB-08).
7. **Secure by default.** DRF's default permission is `IsAuthenticated`; public endpoints must opt in explicitly with `AllowAny`.

Larger decisions are recorded in [`docs/DECISIONS.md`](docs/DECISIONS.md).

## Getting started

**Prerequisites:** Python 3.12, Docker (for Postgres/Redis/Mailpit), Git.

```bash
# 1. Clone and create a virtualenv
git clone <repo-url> rmi-backend && cd rmi-backend
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install dependencies and git hooks
make install                       # or: pip install -r requirements/dev.txt && pre-commit install

# 3. Configure environment
cp .env.example .env               # then set DJANGO_SECRET_KEY

# 4. Start local services and set up the database
make up                            # Postgres :5432, Redis :6379, Mailpit :8025
make migrate
make superuser

# 5. Run
make run                           # http://localhost:8000
```

Then open:

| URL | What |
|---|---|
| http://localhost:8000/api/v1/health/ | Health check |
| http://localhost:8000/api/docs/ | Swagger UI |
| http://localhost:8000/api/redoc/ | Redoc |
| http://localhost:8000/admin/ | Django admin |
| http://localhost:8025 | Mailpit (catches all outgoing email) |

Background jobs (needed once digests and imports land): `make worker` and `make beat` in separate terminals.

## Environment variables

| Variable | Required | Example | Notes |
|---|---|---|---|
| `DJANGO_SETTINGS_MODULE` | yes | `config.settings.dev` | `dev`, `test` or `prod` |
| `DJANGO_SECRET_KEY` | yes | — | Long random string; never commit |
| `DJANGO_DEBUG` | no | `True` | Forced off in prod |
| `DJANGO_ALLOWED_HOSTS` | prod | `api.rmi.org` | Comma-separated |
| `DATABASE_URL` | yes | `postgres://rmi:rmi@localhost:5432/rmi` | |
| `REDIS_URL` | yes | `redis://localhost:6379/0` | Cache + Celery broker |
| `CORS_ALLOWED_ORIGINS` | yes | `http://localhost:3000` | Next.js origin(s), comma-separated |
| `FRONTEND_URL` | yes | `http://localhost:3000` | Used to build links in emails |
| `EMAIL_URL` | no | `smtp://localhost:1025` | Defaults to console backend |
| `DEFAULT_FROM_EMAIL` | no | `RMI <no-reply@rmi.org>` | |

Payment, storage and captcha keys will be added here as their sprints land.

## Everyday commands

| Command | Does |
|---|---|
| `make run` | Dev server on :8000 |
| `make migrations` / `make migrate` | Create / apply migrations |
| `make test` | Run the test suite |
| `make cov` | Tests with coverage report |
| `make lint` / `make format` | Ruff check / auto-fix and format |
| `make check` | Everything CI runs — use before opening a PR |
| `make worker` / `make beat` | Celery worker / scheduler |
| `make shell` | Django shell |

## API conventions

- **Base path:** `/api/v1/`. Breaking changes go to a new version; old versions keep working (SRS 6.1).
- **Format:** JSON, `snake_case` fields.
- **IDs:** UUIDs for users and any resource exposed in URLs.
- **Datetimes:** ISO 8601 in UTC. Deadlines also carry an explicit `timezone` field so the frontend can display the funder's cutoff correctly.
- **Pagination:** `?page=2&page_size=50` (max 100). Response shape: `{count, next, previous, results}`.
- **Filtering / ordering:** `django-filter` query params, plus `?ordering=-published_at`.
- **Errors:** always the same envelope:

  ```json
  {
    "error": {
      "code": "validation_error",
      "message": "Invalid input.",
      "details": { "email": ["This field is required."] }
    }
  }
  ```

- **Gated content:** locked resources return `200` with `"locked": true` and `"unlock_plan"` rather than `403`, so previews still render.
- **Authentication:** designed in Sprint 1 and documented here when it lands.
- **Schema:** the OpenAPI schema at `/api/schema/` is the contract with the frontend. Keep `extend_schema` annotations accurate.

## Testing

```bash
make test               # quick run
make cov                # with coverage
pytest apps/accounts    # one app
pytest -k email         # by name
```

- Tests live in `apps/<app>/tests/`, one file per concern (`test_models.py`, `test_api.py`, …).
- Use factories from `apps/<app>/tests/factories.py`; shared fixtures (`api_client`, `user`, `auth_client`) are in the root `conftest.py`.
- Billing rules, entitlements and access-tier checks need tests for **both** the allowed and the locked path.
- CI runs against real PostgreSQL. The suite is Postgres-first; search features will not work on SQLite.

## Contributing workflow

**Branches**

- `main` — production-ready, deployed.
- `develop` — integration branch; staging deploys from here.
- `feat/<short-name>`, `fix/<short-name>`, `chore/<short-name>` — branched from `develop`.

**Commits** follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(accounts): add email verification endpoint
fix(billing): handle duplicate Paystack webhook
chore: bump django to 5.2.17
```

**Pull request checklist**

- [ ] `make check` passes locally
- [ ] New models inherit the right base classes (see [Core design rules](#core-design-rules))
- [ ] Migrations included and reviewed
- [ ] Endpoints have permissions set explicitly and OpenAPI annotations
- [ ] Tests cover the happy path and the permission/locked path
- [ ] README or `docs/DECISIONS.md` updated if behaviour or architecture changed

## Roadmap

Phase 1 is a 12-week build. Sprint status is updated as work lands.

| Sprint | Weeks | Deliverable | Status |
|---|---|---|---|
| 0 | 1 | Foundation: repo, settings, CI, base models, health check, custom user | 🟡 In progress |
| 1 | 2–3 | Accounts & organizations: registration, verification, login, password reset, profiles, org profiles, invitations, seats, staff roles | ⬜ |
| 2 | 4–5 | Research repository: taxonomy, publications, attachments, datasets, secure downloads, search | ⬜ |
| 3 | 6–7 | Opportunities: listings, filters, lifecycle, public submissions, saved searches, digests, weekly bulletin | ⬜ |
| 4 | 8–9 | Subscriptions & payments: plans, entitlements, checkout, webhooks, manual activation | ⬜ |
| 5 | 10–11 | Observatory & CMS: indicators, bulk upload, country hubs, situation reports, pages, newsletter | ⬜ |
| 6 | 12 | Launch hardening: security review, 2FA for staff, backups, docs, handover | ⬜ |

Sprints 2–3 use a preliminary entitlement check (tier-based) that switches to full plan-based entitlements when billing lands in Sprint 4.

**Phase 2:** policy tracker, expert directory, custom dashboards, usage reporting.
**Phase 3:** early-warning alerts, academy, consultancy engagements.

## License

Proprietary. © Regional Migration Intelligence. All rights reserved. Not for redistribution.
