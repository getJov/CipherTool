# Migrate MySQL App to PostgreSQL

## Why
CipherTool currently depends on local MySQL/MariaDB through `Flask-MySQLdb`, but the deployment target is Render for Flask and Supabase for hosted PostgreSQL. The project also needs a safe MySQL snapshot branch before conversion so the old version can be recovered without maintaining a second repository.

## What
Create a single GitHub repository workflow with a frozen `mysql-version` branch and an active PostgreSQL-ready `main` branch. Protect secrets with `.gitignore` and `.env` handling, push the sanitized MySQL version to `mysql-version` first, then migrate `main` to PostgreSQL/Supabase only after that push succeeds.

## Context

**Relevant files:**
- `app.py` - Flask routes, PostgreSQL connection handling, local login/register flow, and current TOTP verification flow.
- `db/web_app_db.sql` - PostgreSQL schema for the `users` table.
- `plans/06042026-no-ticket-migrate-mysql-to-postgresql/migrations/pgsql.sql` - PostgreSQL/Supabase migration artifact.
- `templates/googleAuth.html` - displays the Authenticator QR and accepts the verification code.
- `templates/login.html` - local login form that starts the verification flow.
- `templates/register.html` - local registration form that creates local users.
- `requirements.txt` - Python package pins for Flask, PostgreSQL, QR, and TOTP support.
- `.gitignore` - ignores `.env`, OAuth client secrets, virtualenvs, generated QR files, local database data, and archives.
- `.env.example` - should document safe placeholder environment variables only.
- `README.md` - documents PostgreSQL/Supabase setup, Render deployment, and manual database-change steps.
- `render.yaml` or Render dashboard settings - needed if deployment config is committed instead of configured manually.

**Patterns to follow:**
- Keep runtime secrets in environment variables, matching existing `get_required_env()` behavior in `app.py`.
- Keep database schema in `db/` or provider migration files, not embedded in route handlers.
- Keep one repo with branches: `mysql-version` for historical MySQL state, `main` for PostgreSQL work.
- Keep Supabase database changes as SQL files in the repo even when applying them manually in the Supabase SQL Editor.
- For production schema changes, run the Supabase SQL manually before pushing code that depends on the new column to `main`, because Render auto-deploys from `main`.

**Key decisions already made:**
- Do not create two repositories.
- Do not create or push `CipherTool_MySQL_version.zip`.
- Do not push `.env`, OAuth client secrets, local MySQL data folders, or raw local database server files.
- Sanitize seeded user rows before pushing to GitHub; no real emails, real password hashes, or local user data should be committed.
- Push the sanitized MySQL version to `mysql-version` first. PostgreSQL conversion starts only after that push succeeds.
- Use Supabase PostgreSQL as the deployed database target.
- Use Render for Flask hosting.
- Google Cloud OAuth configuration is not involved in Authenticator QR/manual key setup. No Google Client settings are required for the TOTP mobile fix.
- Supabase database changes are applied manually in the Supabase SQL Editor for now; no Supabase CI/CD pipeline is part of this work.
- T1-T5 are completed prerequisite work. Current active execution scope is T6-T8 only.
- Persisted per-user TOTP applies to local username/password users only. Google OAuth users remain on the existing OAuth path and are not assigned a `users.totp_secret` in this revision.
- T6 must be executed separately and then stop. T7-T8 must not begin until the user confirms the Supabase SQL has been manually applied, or Render auto-deploy has been paused.

## Constraints

**Must:**
- Preserve a recoverable MySQL baseline before PostgreSQL conversion.
- Fix Git hygiene before the first real commit/push.
- Add `client_secret.json`, local database files, archives, and generated runtime artifacts to `.gitignore`.
- Keep sensitive values in `.env` locally and Render/Supabase/GitHub secrets remotely.
- Use a committed `.env.example` with placeholder keys only.
- Push a sanitized MySQL baseline to the remote `mysql-version` branch before modifying `main` for PostgreSQL.
- Convert database access to a PostgreSQL-compatible driver/library.
- Convert `db/web_app_db.sql` into PostgreSQL-compatible schema/seed SQL or Supabase migration SQL.
- Verify login, register, lockout attempts, and existing cipher routes after migration.
- Add per-user TOTP secret storage without requiring Google Cloud OAuth changes.
- Document and apply the manual Supabase SQL before deploying code that reads/writes `totp_secret`.
- Treat `totp_secret` as sensitive data: do not log it, do not include it in flash messages, and only display it to the active local user during Authenticator setup.
- Generate QR codes per request as an in-memory/base64 data URI instead of writing a shared `static/qrcode.png` file.

**Must not:**
- Commit `.env`, `client_secret.json`, raw `.mysql-data/`, `.mysql-test-data/`, virtualenvs, or production secrets.
- Create or push `CipherTool_MySQL_version.zip`.
- Merge PostgreSQL changes back into `mysql-version`.
- Introduce a second database abstraction layer unless needed for correctness.
- Refactor unrelated cipher, QR, UI, or OAuth behavior during the database migration.
- Change Google OAuth client settings for Authenticator setup.
- Push production code that writes `users.totp_secret` before the Supabase column exists.
- Persist TOTP secrets for Google OAuth-only users in this revision.
- Log or expose `totp_secret` outside the setup/verification page for the active local user.
- Continue writing Authenticator setup QR images to a shared `static/qrcode.png` path.

**Out of scope:**
- Replacing local authentication with Supabase Auth.
- Adding new app features.
- Production-grade backup automation.
- Multi-environment staging/prod Supabase branching.
- Large authentication redesign.
- Supabase migration CI/CD.
- Google OAuth client configuration changes for TOTP.

## Risk

**Level:** 3

**Risks identified:**
- Sensitive files are currently present in the worktree (`.env`, `client_secret.json`, local MySQL data). -> **Mitigation:** Update `.gitignore` before commit, audit staged files with `git status`, and only commit sanitized source files.
- The local `.git` directory appears incomplete/empty, so Git history may not exist in this folder. -> **Mitigation:** If this is the intended repo root, initialize Git, create `main`, connect the remote only after secret audit, push `mysql-version`, then return to `main` for PostgreSQL work. If this is not the intended repo root, stop and move to the real repo before executing.
- Committing seeded user rows exposes emails and password hashes. -> **Mitigation:** Sanitize `db/web_app_db.sql` before the MySQL baseline commit so only schema and safe demo data are pushed.
- MySQL boolean and auto-increment behavior differ from PostgreSQL. -> **Mitigation:** Convert `tinyint(1)` to `boolean`, `int AUTO_INCREMENT` to identity/serial semantics, and test app reads/writes.
- Direct DB code is mixed into route handlers. Future-us will hate deeper database changes if this grows. -> **Mitigation:** For this migration, keep edits minimal; optionally extract DB helpers in a later plan if the app expands.
- Current TOTP uses one global in-memory secret for all users and changes on restart. -> **Mitigation:** Store a per-user `totp_secret` in PostgreSQL and verify codes against the logged-in user's stored secret.
- Mobile users cannot scan a QR code displayed on the same device. -> **Mitigation:** Keep QR setup but also display a manual setup key with copy support.
- Render auto-deploy can ship code before Supabase has the new column. -> **Mitigation:** Apply `ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret varchar(64);` in Supabase SQL Editor before pushing the TOTP code to `main`, or temporarily disable Render auto-deploy until the SQL is applied.
- `totp_secret` must be stored in readable form to verify TOTP codes. -> **Mitigation:** Treat the column as sensitive operational data, never log it, and only show it to the active local user during setup.
- Shared QR image writes can leak or overwrite another user's Authenticator setup. -> **Mitigation:** Render the QR as a request-local base64 data URI and stop using `static/qrcode.png` for Authenticator setup.

**Pushback:**
- Do not create a zip backup for GitHub. A branch is the right backup mechanism here; zip archives invite secret/data leakage and duplicate state.
- This migration should not become an auth rewrite. Supabase Auth is tempting, but it is different work with different risk.
- A global TOTP secret is not acceptable. It breaks after Render restarts and makes all local users share the same Authenticator secret.

## Tasks

### T1: Git Hygiene
**Do:** Update `.gitignore` coverage for secrets, archives, local DB files, generated files, and virtualenvs. Ensure `.env.example` has placeholders only. Confirm `.env` contains real local secrets but is untracked. Sanitize `db/web_app_db.sql` so it contains schema and safe demo data only, or schema only.
**Files:** `.gitignore`, `.env.example`, `db/web_app_db.sql`
**Verify:** `git status --short`; `git ls-files .env client_secret.json .mysql-data .mysql-test-data CipherTool_MySQL_version.zip` returns no tracked sensitive files; `db/web_app_db.sql` contains no real emails, real password hashes, or local-only user data.

### T2: MySQL Baseline Branch
**Do:** If no valid Git repository exists, initialize Git in the project root, create `main`, and commit the sanitized MySQL baseline. Create `mysql-version` from that baseline and push `mysql-version` to the GitHub remote. Do not start PostgreSQL conversion until this push succeeds.
**Files:** Git metadata, sanitized tracked project files
**Verify:** `git branch --show-current`; `git status --short`; `git ls-files .env client_secret.json .mysql-data .mysql-test-data CipherTool_MySQL_version.zip` returns no tracked sensitive files; remote `mysql-version` branch exists after push.

### T3: PostgreSQL Schema and Dependencies
**Do:** Replace MySQL/MariaDB schema with PostgreSQL-compatible schema for `users`. Convert `id` to generated identity, `blocked` to boolean, defaults to PostgreSQL syntax, and preserve required columns. Replace MySQL Python dependencies with PostgreSQL-compatible dependencies.
**Files:** `db/web_app_db.sql`, `requirements.txt`, `plans/06042026-no-ticket-migrate-mysql-to-postgresql/migrations/pgsql.sql`
**Verify:** Apply schema to a local PostgreSQL or Supabase database; confirm `users` exists with expected columns, defaults, and primary key.

### T4: Flask PostgreSQL Integration
**Do:** Replace `Flask-MySQLdb` initialization and query execution with PostgreSQL/Supabase connection handling. Use `DATABASE_URL` or explicit Postgres env vars. Keep existing auth behavior and parameterized SQL. Ensure cursors return dictionary-like rows or adapt row access safely.
**Files:** `app.py`, `.env.example`, `README.md`
**Verify:** Run the app locally against PostgreSQL; manually verify registration, login, failed login attempt counting, blocked account behavior, Google OAuth redirect path, and cipher page access.

### T5: Render and Supabase Deployment Readiness
**Do:** Document or add deploy configuration for Render Flask hosting and Supabase Postgres environment variables. Include `gunicorn` if needed. Document GitHub branch behavior: deploy `main`, keep `mysql-version` frozen.
**Files:** `requirements.txt`, `README.md`, `render.yaml` if used
**Verify:** Render build command installs dependencies; start command uses `gunicorn app:app`; required env vars are listed and no secrets are committed; run `python -m compileall app.py` and a basic Flask import/startup check.

### T6: Per-User TOTP Schema
**Do:** Add nullable `totp_secret varchar(64)` to the `users` table. Update the local PostgreSQL schema and plan migration artifacts. Add a standalone SQL migration file that can be manually run in Supabase SQL Editor.
**Files:** `db/web_app_db.sql`, `plans/06042026-no-ticket-migrate-mysql-to-postgresql/migrations/pgsql.sql`, `plans/06042026-no-ticket-migrate-mysql-to-postgresql/migrations/mssql.sql`, `plans/06042026-no-ticket-migrate-mysql-to-postgresql/migrations/knexmigration.js`, `db/migrations/20260605_add_totp_secret.sql`
**Verify:** Apply the SQL locally and confirm `users.totp_secret` exists using `SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'totp_secret';`. Manual Supabase SQL must be documented as `ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret varchar(64);`. Stop after T6 and require user confirmation that the same SQL has been run in Supabase, or that Render auto-deploy is temporarily paused, before T7 starts.

### T7: Authenticator Manual Setup Flow
**Do:** Replace the global in-memory `keyQR` with persisted `totp_secret` storage for local username/password users. Generate a secret for local users that do not have one, persist it to PostgreSQL, render the QR code from that secret as a request-local base64 data URI, show the manual setup key on the verification page, and add a copy-to-clipboard control for mobile users. Verify submitted codes against the stored secret for the active local user. Leave Google OAuth-only users out of persisted TOTP for this revision.
**Files:** `app.py`, `templates/googleAuth.html`, `static/style.css`, optional `static/app.js`
**Verify:** Register or log in locally, open verification on mobile-width viewport, confirm the QR still displays without writing `static/qrcode.png`, confirm the manual key is visible/copyable, confirm the code input uses `autocomplete="one-time-code"`, and confirm a valid Authenticator code verifies against the user's stored secret after an app restart. Confirm Google OAuth login behavior is not expanded beyond current scope.

### T8: TOTP Deployment Instructions
**Do:** Update documentation with the manual Supabase SQL step for `totp_secret`, local schema load instructions, and a note that no Google OAuth client changes are needed for Authenticator setup.
**Files:** `README.md`, `plans/06042026-no-ticket-migrate-mysql-to-postgresql/spec.md`
**Verify:** README includes manual Supabase SQL instructions and Render remains auto-deploy-from-`main`.

## Done
### Completed Prerequisite Criteria
- [ ] Sanitized MySQL baseline exists in Git before PostgreSQL conversion begins.
- [ ] `mysql-version` branch exists on the GitHub remote and is not polluted by PostgreSQL changes.
- [ ] `.gitignore` prevents committing `.env`, OAuth secrets, local DB files, archives, virtualenvs, caches, and generated runtime files.
- [ ] `.env.example` documents required placeholder values without secrets.
- [ ] `db/web_app_db.sql` contains no real emails, real password hashes, or local-only user data.
- [ ] PostgreSQL schema can be applied to Supabase/Postgres.
- [ ] Flask app runs against PostgreSQL using environment variables.
- [ ] Register/login/lockout/cipher routes are verified.
- [ ] Render deployment requirements are documented or configured.
- [ ] No sensitive files are tracked by Git.

### Active Rev 2 Criteria
- [ ] `users.totp_secret` exists locally and the manual Supabase SQL is documented.
- [ ] T6 stops before app code changes, and user confirms Supabase SQL has been run or Render auto-deploy is paused before T7-T8.
- [ ] Authenticator setup works on mobile without scanning by using the manual setup key.
- [ ] TOTP verification uses per-user persisted secrets and survives app restart.
- [ ] Authenticator QR is rendered per request and no longer uses shared `static/qrcode.png`.
- [ ] `totp_secret` is not logged and is only displayed to the active local user during setup.
- [ ] Google OAuth-only users are not pulled into persisted local-user TOTP in this revision.
- [ ] Google OAuth settings are not changed for this TOTP work.

## Revision Log

### Rev 1 - 2026-06-04
**Change:** Removed `CipherTool_MySQL_version.zip` backup workflow. Required a sanitized `mysql-version` branch push before PostgreSQL conversion on `main`.
**Reason:** Branch-based backup is safer and avoids pushing archive files that may contain secrets or local database data.
**Updated Done criteria:** Remote `mysql-version` branch must exist before conversion, zip archive is out of scope, and seeded SQL must be sanitized before push.

### Rev 2 - 2026-06-05
**Change:** Added mobile-friendly Authenticator setup: per-user `totp_secret`, QR plus manual setup key with copy support, and manual Supabase SQL instructions.
**Reason:** Mobile users cannot reliably scan a QR code shown on the same device, and the current global in-memory TOTP secret is not durable or user-specific.
**Updated Done criteria:** Local and Supabase schema include `totp_secret`; verification uses persisted per-user secrets for local users only; manual setup key works on mobile; no Google OAuth client changes are required.

### Rev 3 - 2026-06-05
**Change:** Clarified active execution scope as T6-T8 only, required a hard stop after T6 before TOTP app code, scoped persisted TOTP to local username/password users, and required request-local QR rendering instead of shared `static/qrcode.png`.
**Reason:** Prevent spec-code drift around already-completed migration work, avoid breaking Google OAuth-only users, prevent Render auto-deploy from racing ahead of Supabase schema, and remove shared QR overwrite/leak risk.
**Updated Done criteria:** T6 must stop for user confirmation; T7-T8 only proceed after Supabase SQL is applied or auto-deploy is paused; QR uses a per-request data URI; `totp_secret` is treated as sensitive.
