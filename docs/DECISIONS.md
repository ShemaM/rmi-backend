# Architecture Decision Log

Short, dated records of decisions that shape the codebase. Add a new entry instead of
editing an old one; if a decision is reversed, add a new entry that supersedes it.

| ID | Date | Decision | Why |
|----|------|----------|-----|
| ADR-001 | 2026-09-27 | Django 5.2 LTS + DRF, one modular monolith (`apps/*`) | SRS priority 3 "Unified Architecture"; LTS support to April 2028 |
| ADR-002 | 2026-09-27 | PostgreSQL is the only supported database | Full-text search and trigram typo tolerance (SRS 4.3) without an extra search service in Phase 1 |
| ADR-003 | 2026-09-27 | Custom `accounts.User` (UUID pk, email login) from the first migration | Swapping the user model later is costly; UUIDs avoid leaking user counts in URLs |
| ADR-004 | 2026-09-27 | Every model inherits `core.TimeStampedModel`; editorial models also `SoftDeleteModel` + `HistoricalRecords` | SRS D5 (revision history) and D6 (archive, never hard-delete) |
| ADR-005 | 2026-09-27 | DRF default permission is `IsAuthenticated`; public endpoints opt in | Paid content is the revenue model (SRS priority 4) — fail closed |
| ADR-006 | 2026-09-27 | All API errors use `{"error": {code, message, details}}` | One error-handling path in the Next.js client |
