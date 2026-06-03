# Migrate MySQL App to PostgreSQL

## Why
CipherTool currently depends on local MySQL/MariaDB through `Flask-MySQLdb`, but the deployment target is Render for Flask and Supabase for hosted PostgreSQL. The project also needs a safe MySQL snapshot branch before conversion so the old version can be recovered without maintaining a second repository.

## What
Create a single GitHub repository workflow with a frozen `mysql-version` branch and an active PostgreSQL-ready `main` branch. Protect secrets with `.gitignore` and `.env` handling, push the sanitized MySQL version to `mysql-version` first, then migrate `main` to PostgreSQL/Supabase only after that push succeeds.

## Context

**Relevant files:**
- `app.py` - Flask routes, MySQL config, and SQL queries using `mysql.connection.cursor()`.
- `db/web_app_db.sql` - MariaDB/phpMyAdmin dump for the `users` table and seeded rows.
- `requirements.txt` - currently includes MySQL packages: `Flask-MySQLdb` and `mysqlclient`.
- `.gitignore` - already ignores `.env`, virtualenvs, generated QR files, and local MySQL data, but does not ignore `client_secret.json`.
- `.env.example` - should document safe placeholder environment variables only.
- `README.md` - currently documents local MySQL setup and must be updated for PostgreSQL/Supabase.
- `render.yaml` or Render dashboard settings - needed if deployment config is committed instead of configured manually.

**Patterns to follow:**
- Keep runtime secrets in environment variables, matching existing `get_required_env()` behavior in `app.py`.
- Keep database schema in `db/` or provider migration files, not embedded in route handlers.
- Keep one repo with branches: `mysql-version` for historical MySQL state, `main` for PostgreSQL work.

**Key decisions already made:**
- Do not create two repositories.
- Do not create or push `CipherTool_MySQL_version.zip`.
- Do not push `.env`, OAuth client secrets, local MySQL data folders, or raw local database server files.
- Sanitize seeded user rows before pushing to GitHub; no real emails, real password hashes, or local user data should be committed.
- Push the sanitized MySQL version to `mysql-version` first. PostgreSQL conversion starts only after that push succeeds.
- Use Supabase PostgreSQL as the deployed database target.
- Use Render for Flask hosting.

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

**Must not:**
- Commit `.env`, `client_secret.json`, raw `.mysql-data/`, `.mysql-test-data/`, virtualenvs, or production secrets.
- Create or push `CipherTool_MySQL_version.zip`.
- Merge PostgreSQL changes back into `mysql-version`.
- Introduce a second database abstraction layer unless needed for correctness.
- Refactor unrelated cipher, QR, UI, or OAuth behavior during the database migration.

**Out of scope:**
- Replacing local authentication with Supabase Auth.
- Adding new app features.
- Production-grade backup automation.
- Multi-environment staging/prod Supabase branching.
- Large authentication redesign.

## Risk

**Level:** 3

**Risks identified:**
- Sensitive files are currently present in the worktree (`.env`, `client_secret.json`, local MySQL data). -> **Mitigation:** Update `.gitignore` before commit, audit staged files with `git status`, and only commit sanitized source files.
- The local `.git` directory appears incomplete/empty, so Git history may not exist in this folder. -> **Mitigation:** If this is the intended repo root, initialize Git, create `main`, connect the remote only after secret audit, push `mysql-version`, then return to `main` for PostgreSQL work. If this is not the intended repo root, stop and move to the real repo before executing.
- Committing seeded user rows exposes emails and password hashes. -> **Mitigation:** Sanitize `db/web_app_db.sql` before the MySQL baseline commit so only schema and safe demo data are pushed.
- MySQL boolean and auto-increment behavior differ from PostgreSQL. -> **Mitigation:** Convert `tinyint(1)` to `boolean`, `int AUTO_INCREMENT` to identity/serial semantics, and test app reads/writes.
- Direct DB code is mixed into route handlers. Future-us will hate deeper database changes if this grows. -> **Mitigation:** For this migration, keep edits minimal; optionally extract DB helpers in a later plan if the app expands.

**Pushback:**
- Do not create a zip backup for GitHub. A branch is the right backup mechanism here; zip archives invite secret/data leakage and duplicate state.
- This migration should not become an auth rewrite. Supabase Auth is tempting, but it is different work with different risk.

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

## Done
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

## Revision Log

### Rev 1 - 2026-06-04
**Change:** Removed `CipherTool_MySQL_version.zip` backup workflow. Required a sanitized `mysql-version` branch push before PostgreSQL conversion on `main`.
**Reason:** Branch-based backup is safer and avoids pushing archive files that may contain secrets or local database data.
**Updated Done criteria:** Remote `mysql-version` branch must exist before conversion, zip archive is out of scope, and seeded SQL must be sanitized before push.
