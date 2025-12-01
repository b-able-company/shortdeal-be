# ShortDeal Implementation Plan

## Scope & Guardrails
- Deliver P0 items only (docs/func-spec.md, 65 features) using Django 4.2, DRF, JWT, PostgreSQL.
- Follow response envelope `{success, data, message, pagination?, meta?}` and base URL `/api/v1/`.
- Enforce business rules: producer signup → booth auto-create, single pending offer per content/buyer, offer accept → LOI auto-create, onboarding gate, email notifications, soft delete via `status='deleted'`.
- No raw SQL, no custom user beyond AbstractUser extension, UTC timestamps, ArrayField for tags, foreign keys default CASCADE.

## Required Validations (done before coding)
- **Edge case analysis**
  - Auth/Onboarding: duplicate email, weak/ mismatched passwords, role change attempts, onboarding re-entry after completion, invalid logo/thumbnail (type/size), slug collisions for booths, onboarding access when not authenticated or wrong role.
  - Content browsing: invalid filters (price range inversion, bad currency), accessing deleted content, view_count increments, empty list states.
  - Content management: edit/delete by non-owner, delete with existing offers, soft delete visibility, missing required fields, invalid URLs, oversized thumbnails, genre count outside 1-3, onboarding incomplete producer.
  - Offers: submitting on deleted/non-public content, buyer submitting twice (pending uniqueness), expired offers actions, accept/reject on non-owner producer, invalid validity_days, currency mismatch, concurrent accept/reject race.
  - LOI: access by non-related party, missing PDF yet (503), duplicate LOI generation guard, pagination correctness.
  - Settings/Admin: password change with wrong current password, profile updates violating length limits, admin endpoints accessed by non-admin.
- **Documentation consistency check**
  - IA URLs and access matrix align with API list (docs/ia.md ↔ docs/api-spec.md). Functional IDs map to endpoints in api-spec.md; no conflicts found.
  - Response format: AGENTS.md defines `{success, data, message, pagination?}`; api-spec.md also includes optional `meta`—implement `meta` as optional.
  - Permission mapping consistent across docs/permissions.md and IA matrix; onboarding gate noted in both func-spec and AGENTS business rules.
- **Data model validation**
  - db-schema.md tables (users, booths, contents, offers, loi_documents) cover required fields/constraints from func-spec/api-spec: ArrayField tags, soft delete via `status`, offer uniqueness `(content_id, buyer_id, status='pending')`, LOI 1:1 with offer and numbering, CASCADE defaults.
  - Currency, length limits, validity_days check constraints align with specs; no missing fields detected for P0.

## Implementation Plan (ordered)
- Foundations
  - Centralize DRF settings: JWT (simplejwt), default permissions/auth classes, pagination 20/page, response envelope helper, exception handler with error codes.
  - Core app: permission classes per docs/permissions.md, onboarding middleware/decorator, status constants, soft-delete manager/queryset.
  - File upload endpoint with validation (logo/thumbnail types, sizes).
- Accounts/Auth/Onboarding
  - Extend AbstractUser with required fields (user_type, onboarding fields, company_name, country, genre_tags, booth_slug, is_onboarded).
  - Serializers/views for register/login/refresh/me/logout; enforce role immutability.
  - Onboarding producer/buyer endpoints: validation per spec, logo upload handling, booth slug generation; block if already onboarded.
  - Signals: producer creation → booth auto-create; update onboarding flags.
- Booths & Content Browsing
  - Booth model (1:1 producer) and public read endpoint (`/booths/{slug}/`) with contents listing.
  - Public content list/detail endpoints with filters/sorting, view_count increment (async safe hook).
  - Pagination standard response; soft-delete filter for public endpoints.
- Content Management (Producer)
  - CRUD endpoints under `/studio/contents/` with IsProducer+IsOwner+IsOnboarded; multipart support for create/update.
  - Delete: soft delete only, block if offers exist; return 422 code structure.
  - Offer count for producer listing summary.
- Offers
  - Buyer create endpoint with uniqueness guard and expiry calculation; email notification trigger.
  - Buyer list/detail endpoints with IsOwner filter; status filters and expires_at handling.
  - Producer list/detail endpoints; summary counts; IsOwner producer check.
  - Accept/Reject actions: state transition guards, responded_at, signal to create LOI on accept, email notifications.
  - Scheduled task for expiring offers (Celery beat hook).
- LOI
  - Model + serializer for LOI snapshot; 1:1 with offer.
  - List/detail endpoints restricted to related parties; include content/party snapshots.
  - PDF generation task & download endpoint; handle generating state with 503 code.
- Notifications
  - Email hooks for NTF-001~004 using send_mail(); template stubs and configurable sender.
- Settings
  - Profile GET/PATCH for authenticated users with role-aware fields; change-password endpoint with current password check.
- Admin
  - Admin dashboard endpoint (summary + recent lists) with IsAdmin; period filter (7d/30d).
- Testing & QA
  - Unit/DRF tests per feature: auth/onboarding, content public, producer CRUD, offers (buyer/prod flows), LOI access, settings, admin.
  - Cover edge cases: duplicate pending offer, delete with offers, unauthorized access, onboarding gate, PDF generating response, pagination metadata.
  - Add factory fixtures and test helpers; use pytest if configured (or Django test).

## Deliverables & Next Steps
- Implement per order above, committing after major modules (accounts/onboarding → contents → offers/LOI → settings/admin).
- Keep docs in sync if APIs deviate; update OpenAPI via drf-spectacular after endpoint completion.
