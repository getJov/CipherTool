# CipherTool

Local Flask app for classic cipher tools with local login, Google OAuth, TOTP verification, and QR generation.

## Local Setup

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### 2. Install Python dependencies

`Flask-MySQLdb` uses `mysqlclient`, which needs MySQL/MariaDB client development headers before installation.

Ubuntu/Debian prerequisite:

```bash
sudo apt install mysql-server default-libmysqlclient-dev build-essential pkg-config
```

Then install the app dependencies:

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
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=replace-with-your-local-db-password
MYSQL_DB=web_app_db
GOOGLE_CLIENT_ID=replace-with-google-client-id
GOOGLE_CLIENT_SECRET=replace-with-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/callback
```

Do not commit `.env`.

### 4. Start MySQL

Ubuntu/Debian:

```bash
sudo systemctl start mysql
mysqladmin ping
```

If `mysqladmin ping` cannot connect, start or repair the local MySQL service before running the app.

### 5. Load the local database

Importing this SQL file resets the local seeded `users` table.

```bash
mysql -u root -p < db/web_app_db.sql
mysql -u root -p -e "SELECT COUNT(*) FROM web_app_db.users;"
```

### 6. Run the app

```bash
python app.py
```

Open `http://localhost:5000`.
