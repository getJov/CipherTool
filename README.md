# CipherTool

Flask app for classic cipher tools with local login, Google OAuth, TOTP verification, QR generation, and PostgreSQL-backed user accounts.

## Local Setup

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a local `.env` from the example and fill in local-only values:

```bash
cp .env.example .env
```

Required keys:

```text
SECRET_KEY=replace-with-a-local-secret-key
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/web_app_db
DATABASE_SSLMODE=prefer
GOOGLE_CLIENT_ID=replace-with-google-client-id
GOOGLE_CLIENT_SECRET=replace-with-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/callback
```

Do not commit `.env`.

For Supabase, use the PostgreSQL connection string from the Supabase dashboard as `DATABASE_URL`. Use `DATABASE_SSLMODE=require` unless the connection string already includes an SSL mode.

### 4. Create a PostgreSQL database

Ubuntu/Debian:

```bash
sudo apt install postgresql
sudo systemctl start postgresql
createdb web_app_db
```

If you use Supabase instead of a local database, create the project in Supabase and run the schema in the SQL editor.

### 5. Load the database schema

```bash
psql "$DATABASE_URL" -f db/web_app_db.sql
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM users;"
```

### 6. Run the app

```bash
python3 app.py
```

Open `http://localhost:5000`.

## Render + Supabase Deployment

Deploy the PostgreSQL version from the `main` branch. Keep `mysql-version` frozen as the old MySQL baseline.

Render settings:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
Branch: main
```

Required Render environment variables:

```text
SECRET_KEY
DATABASE_URL
DATABASE_SSLMODE=require
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI=https://your-render-service.onrender.com/callback
```

Run `db/web_app_db.sql` in Supabase before starting the Render service. Do not commit Supabase passwords, Render secrets, Google OAuth secrets, or local `.env` files.

## Manual Supabase Database Changes

Render auto-deploys from `main`, but Supabase database changes are applied manually for this project. Run database SQL in Supabase before deploying app code that depends on the new column.

For the Authenticator mobile setup update, run this in Supabase SQL Editor before deploying the TOTP app-code changes:

```sql
ALTER TABLE users
ADD COLUMN IF NOT EXISTS totp_secret varchar(64);
```

No Google OAuth client changes are required for Authenticator QR/manual setup.

The hosted app uses a per-user Authenticator setup key for local username/password accounts. The verification page shows both a QR code and a manual setup key so mobile users can enter the key directly in Google Authenticator when the QR code is displayed on the same phone.
