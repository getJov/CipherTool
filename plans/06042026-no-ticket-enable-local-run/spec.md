# Enable Local Run

## Why
The app cannot reliably run on a fresh local machine because dependencies, database bootstrap, and page runtime assumptions are incomplete. Fixing this now makes local development reproducible instead of tied to the original Windows virtualenv.

## What
Make the Flask app runnable locally from a fresh checkout with a new Python virtualenv, installed requirements, local environment configuration, and a running local MySQL database loaded from the repo SQL file. Done means the app starts, login/register routes can reach the local database, secrets are read from `.env` instead of hardcoded values, and the main pages do not throw obvious runtime errors during normal local use.

## Context

**Relevant files:**
- `app.py` - Flask app, MySQL config, Google OAuth flow, TOTP QR generation, cipher routes.
- `requirements.txt` - Python dependency contract used for fresh local setup.
- `db/web_app_db.sql` - database dump required by login/register.
- `templates/cipher.html` - main cipher page and inline browser scripts.
- `templates/googleAuth.html` - authenticator page with session display assumptions.
- `static/password.js` - password visibility toggles used by login/register pages.
- `client_secret.json` - currently contains Google OAuth secret data and should no longer contain real secrets after this task.
- `.gitignore` - should exclude local env, virtualenv, caches, and generated local artifacts.
- `.env` - local-only sensitive configuration; must not be committed.
- `.env.example` - non-sensitive template showing required keys.
- `README.md` - local setup and run instructions.
- `installed_packages.txt` - informal install notes; not authoritative.
- Local MySQL 8.0 is installed on this device, but the service was not reachable during context-building.

**Patterns to follow:**
- Keep the single-file Flask app structure for now; this task is about local run stability, not architecture cleanup.
- Use existing templates/static files and add guards around current behavior instead of introducing a frontend build step.
- Keep MySQL/MariaDB as the local database because `flask_mysqldb` and the existing dump already assume it.
- Configure local MySQL credentials through `.env`; the provided local DB password belongs only in `.env`.

**Key decisions already made:**
- Recreate the virtualenv locally instead of using committed `myenv`, because `myenv` points to a Windows Python executable.
- Keep Google OAuth configured for `http://localhost:5000/callback`, but load client values from environment.
- Do not add Docker or a new database abstraction in this task.
- Use `python-dotenv` so local `.env` values load automatically when running `python app.py`.

## Constraints

**Must:**
- Add all import-time dependencies used by `app.py` to `requirements.txt`.
- Replace private `pip._vendor` usage with a real dependency/import.
- Move sensitive/configurable values out of `app.py` and `client_secret.json` usage into `.env`-loaded configuration.
- Create `.gitignore` and ensure `.env`, local secret JSON files, `myenv/`, Python caches, and generated local files are ignored.
- Create `.env.example` with placeholder values only.
- Create local `.env` with current local development values so the app can run in this workspace, including the provided local DB password as `MYSQL_PASSWORD`.
- Remove real secret values from `client_secret.json` or remove the file if it is no longer needed after env migration.
- Add local setup instructions with exact commands for venv creation, dependency install, DB import, and app startup.
- Make database bootstrap explicit enough that `web_app_db` can be created and loaded locally.
- Start or otherwise make the local MySQL service reachable, create/load `web_app_db`, and verify the `users` table exists on this device.
- Keep existing routes and page names stable.
- Validate inputs that currently crash normal app usage.
- Preserve local-only behavior for HTTP OAuth during development.

**Must not:**
- Do not introduce new framework dependencies beyond missing runtime packages already implied by the code.
- Do not commit or document real secrets in `.env.example` or `README.md`.
- Do not write the provided local DB password into `spec.md`, `.env.example`, README, shell history examples, or command output summaries.
- Do not keep using `client_secret.json` for OAuth configuration after env migration.
- Do not refactor the app into blueprints/services.
- Do not change authentication behavior beyond making local routes run.
- Do not modify unrelated styling or redesign pages.
- Do not rely on the committed `myenv`.

**Out of scope:**
- Production deployment hardening.
- Secret rotation.
- Security audit of OAuth/session/database handling.
- Replacing MySQL with SQLite.
- Removing committed virtualenv files from the repo.

## Risk

**Level:** 2

**Risks identified:**
- Hardcoded DB credentials can still fail on machines where root has a password -> **Mitigation:** document exact local assumptions and keep config change minimal unless the user asks for env-based config.
- Google OAuth may fail if the OAuth client is not valid or the browser callback differs from `localhost:5000` -> **Mitigation:** keep local login/register usable and leave OAuth callback unchanged.
- Moving secrets to `.env` can break startup if required variables are missing -> **Mitigation:** add `.env.example`, load with `python-dotenv`, and make missing required config fail with clear messages.
- `mysqlclient` may fail to install without MySQL/MariaDB client headers -> **Mitigation:** document OS-level prerequisites in setup instructions.
- Starting or configuring MySQL may require elevated permission outside the workspace sandbox -> **Mitigation:** request escalation only for the specific service/start/import action when execution reaches that step.
- Changing SQL bootstrap can break users who import into an already-selected database -> **Mitigation:** use standard `CREATE DATABASE IF NOT EXISTS` and `USE web_app_db` before table creation; document whether import is fresh-only or idempotent.
- The provided local DB password can leak through docs or command lines -> **Mitigation:** store it only in `.env`; use `.env`-driven app config and avoid printing the value.
- Browser script null errors hide later app behavior -> **Mitigation:** guard DOM lookups instead of changing UI flow.

**Pushback (if any):**
- The committed virtualenv is codebase decay. It makes the repo look runnable while actually being machine-specific. Future-us will hate this. The better follow-up is to remove `myenv/` from source control and add a clear setup README, but that cleanup is out of this task unless explicitly requested.
- Secrets are committed in `app.py` and `client_secret.json`. Moving them to `.env` improves local handling but does not undo prior exposure. Rotate those credentials later; this task only stops the app from depending on hardcoded secrets.

## Tasks

### T1: Fix import-time local startup dependencies
**Do:** Add missing dependencies for `pyotp`, QR generation, image support, `CacheControl`, and `.env` loading; replace `from pip._vendor import cachecontrol` with a supported import and adjust usage.
**Files:** `requirements.txt`, `app.py`
**Verify:** Active venv: `python -c "import flask, flask_mysqldb, pyotp, qrcode, dotenv; from cachecontrol import CacheControl; import app; print('ok')"`

### T2: Move local configuration and secrets into environment files
**Do:** Create `.gitignore`, `.env`, and `.env.example`; load `SECRET_KEY`, MySQL settings, Google OAuth client settings, and redirect URI from `.env`; remove runtime dependency on `client_secret.json`; remove or sanitize `client_secret.json`; keep `.env.example` placeholder-only.
**Files:** `.gitignore`, `.env`, `.env.example`, `app.py`, `client_secret.json`
**Verify:** Active venv: `python -c "import app; print(app.app.config['MYSQL_DB'])"` reads config from `.env`; manual: `.env` contains `MYSQL_PASSWORD` using the provided local DB password; manual: `.gitignore` includes `.env`, local secret JSON files, and `myenv/`; manual: no real secrets remain in `app.py`, `.env.example`, `README.md`, `spec.md`, or `client_secret.json`.

### T3: Make local database bootstrap explicit
**Do:** Update the SQL dump so it creates/selects `web_app_db` before creating `users`; keep the existing schema and seed data intact.
**Files:** `db/web_app_db.sql`
**Verify:** Manual: import `db/web_app_db.sql` into local MySQL/MariaDB, then confirm `web_app_db.users` exists.

### T4: Configure and load the local MySQL database
**Do:** Verify the local MySQL server is installed; start the local MySQL service if it is not reachable; configure database access to match `.env`; create/load `web_app_db` from `db/web_app_db.sql`; verify the `users` table exists. If starting/configuring the service requires elevated permission, request approval for the narrow MySQL service action.
**Files:** `.env`, `db/web_app_db.sql`
**Verify:** `mysqladmin ping` succeeds; `mysql --defaults-extra-file=<temporary-client-config> -e "SELECT COUNT(*) FROM web_app_db.users;"` succeeds without exposing the password in command text or output.

### T5: Fix route and form crashes during normal local use
**Do:** Ensure `GET /makeQR` returns a valid response or restricts the route correctly; validate blank Vigenere keywords before calling cipher logic; avoid template/session assumptions that raise errors for local and Google sessions.
**Files:** `app.py`, `templates/cipher.html`, `templates/googleAuth.html`
**Verify:** Manual: register/login, complete authenticator step, open `/cipher`, submit Atbash/Caesar/Vigenere including blank-keyword case, open `/myQR`.

### T6: Guard frontend scripts on pages where optional elements are absent
**Do:** Add null checks around password toggle and copy-result handlers so login/register/cipher pages do not throw browser errors before optional elements render.
**Files:** `static/password.js`, `templates/cipher.html`
**Verify:** Manual: load `/local_login`, `/register`, and `/cipher` with browser console open; no null-reference errors on page load.

### T7: Document exact local run steps
**Do:** Add local setup instructions covering Python venv creation, OS-level MySQL/MariaDB prerequisite note, dependency install, `.env` setup from `.env.example`, local MySQL service/start expectations, SQL import, and app startup command.
**Files:** `README.md`
**Verify:** Manual: commands are complete enough for a fresh local setup; no real secrets appear in README.

## Done
- [ ] Fresh virtualenv can install `requirements.txt`.
- [ ] `.gitignore` excludes `.env`, `myenv/`, Python caches, and generated local artifacts.
- [ ] `.env` exists locally with sensitive/configurable values; `.env.example` contains placeholders only.
- [ ] The provided local DB password appears only in `.env`, not in `spec.md`, `.env.example`, README, app source, or command summaries.
- [ ] `app.py` reads Flask secret, MySQL config, and Google OAuth config from environment instead of hardcoded secret values or `client_secret.json`.
- [ ] No real secrets remain in `app.py`, `client_secret.json`, `.env.example`, or README.
- [ ] `python app.py` starts Flask locally on port 5000.
- [ ] Local MySQL is reachable on this device.
- [ ] Database SQL can create/load `web_app_db.users`.
- [ ] `web_app_db.users` exists in local MySQL and can be queried.
- [ ] Register and local login can reach MySQL without setup-related errors.
- [ ] Authenticator and cipher pages load without server/template errors.
- [ ] Browser console has no obvious null-reference errors on login/register/cipher initial load.
- [ ] README contains exact local setup/run commands and no real secrets.
- [ ] No unrelated refactor or redesign included.

## Revision Log

### Rev 1 - 2026-06-04
**Change:** Added `.env`, `.env.example`, `.gitignore`, environment-based config loading, and README/local setup instructions to scope.
**Reason:** User requested sensitive data be moved into `.env` and local run instructions were a readiness blocker.
**Updated Done criteria:** Added checks for ignored local secrets, environment-backed app config, setup documentation, and no real secrets in public templates/docs.

### Rev 2 - 2026-06-04
**Change:** Added explicit local MySQL service/start/import work and required the provided local DB password to be stored only in `.env`.
**Reason:** User wants the database installed/configured locally on this device, not just documented.
**Updated Done criteria:** Added checks for local MySQL reachability, successful `web_app_db.users` query, and password containment only in `.env`.
