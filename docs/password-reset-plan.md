# Password Reset Feature Plan

Goal: let users recover access when they forget their password by requesting a reset email and setting a new password via token validation. Keep responses aligned with the existing `{success, data, message}` envelope and JWT auth model.

## Current State (touchpoints)
- Auth APIs exist for register/login/logout/profile/change-password (`apps/accounts/api_views.py`, `apps/accounts/settings_views.py`) but no forgot/reset flow.
- Response helpers: `apps/core/response.py` (`success_response`, `error_response`), exception handler `apps/core/exceptions.py`.
- Email utility available via `django.core.mail.send_mail` and `apps/notifications/emails.py` patterns.
- Web UI uses Django templates + bootstrap (`templates/accounts/login.html`, `signup.html`, `settings.html`); no reset screens yet.

## API Design (JWT side)
- `POST /api/v1/auth/password-reset/request/` (AllowAny)
  - Body: `{ "email": "user@example.com" }` (case-insensitive).
  - Behavior: if a matching active user exists, issue a one-time token using `PasswordResetTokenGenerator`, compose reset URL (frontend/base URL configurable env), send via `send_mail`. Always return 200 with generic message to avoid user enumeration. Log request for audit/debug.
  - Response: `success: true`, `message: "If the email exists, a reset link has been sent."`, `data: {}`.
  - Errors: 400 only for malformed payload (missing email).
- `POST /api/v1/auth/password-reset/confirm/` (AllowAny)
  - Body: `{ "uid": "<uidb64>", "token": "<token>", "new_password": "...", "new_password_confirm": "..." }`.
  - Behavior: decode uid → user lookup; validate token via `PasswordResetTokenGenerator.check_token`; validate passwords with `validate_password` and match; on success set password, optionally return fresh JWT tokens to reduce friction.
  - Response: `success: true`, `message: "Password has been reset successfully."`, `data: {"tokens": {...}}` only if auto-login is enabled.
  - Errors: 400 for invalid/expired token, mismatch passwords, weak password; 404 if user missing/deleted.
- Optional helper endpoint for UX validation: `GET /api/v1/auth/password-reset/validate/?uid=...&token=...` to let SPA pre-check token; same envelope with `data: {"is_valid": true|false}`.

## Backend Implementation Steps
- Serializer(s):
  - `PasswordResetRequestSerializer` → validates email, stores normalized email, no user leak.
  - `PasswordResetConfirmSerializer` → fields `uid`, `token`, `new_password`, `new_password_confirm`; uses `validate_password`; token verification; sets password.
- Views:
  - Add APIViews in `apps/accounts/api_views.py` (tagged `Authentication`, `AllowAny`) using the serializers and `success_response/error_response`.
  - Wire URLs in `apps/accounts/api_urls.py` under `/api/v1/auth/`.
- Email helper:
  - New function in `apps/notifications/emails.py` to render plain-text reset mail (includes username/company, expiry note, reset URL, support contact).
  - Reset URL base configurable via env (e.g., `FRONTEND_URL` or fallback to Django site domain).
- Token handling:
  - Use `PasswordResetTokenGenerator`; include `user.pk` + `last_login`/`password` hash for invalidation after use; optional throttle per email to prevent abuse.
- Docs:
  - Update `docs/api-spec.md` and `docs/ia.md` with new endpoints, request/response schemas, and access rules; mention no user enumeration.
- Tests:
  - Integration tests for request → email send (use Django outbox) and confirm success/failure cases (invalid token, mismatched passwords, weak password).
  - Unit test for email helper content (includes reset URL) and serializer validation edge cases.

## Web UI (Django templates) Plan
- Screens:
  - `Forgot password` page with email form (`templates/accounts/password_reset_request.html`) using messages for success notice.
  - `Reset password` page (`templates/accounts/password_reset_confirm.html`) accepting new password + confirm; validates token and shows error if invalid/expired.
- URLs/Views:
  - Add routes in `apps/accounts/urls.py` (session-based) for request + confirm; reuse serializers or thin forms that call the same logic/service.
  - Add CTA link on `templates/accounts/login.html` (“Forgot password?”) pointing to the request page.
- UX notes:
  - Keep copy neutral to avoid leaking account existence.
  - After successful reset, redirect to login with success flash; consider auto-login if tokens returned.

## Open Questions
- Should API confirm endpoint return fresh JWT tokens to auto-log-in, or redirect user to login flow?
- Frontend reset URL base: use env (e.g., `FRONTEND_URL`) or Django template route? Provide both?
- Rate limiting: apply DRF throttle class for reset requests to reduce abuse?***
