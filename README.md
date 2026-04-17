# TransferDB

A football transfer management web application built with Flask and MySQL.

## Prerequisites

- Python 3.9+
- MySQL 8.0+ (server running locally)
- `mysql` CLI available in your terminal

---

## Quick Start (Recommended)

The `init.sh` script handles everything — virtual environment, dependencies, schema, seed data, triggers, and app startup — in one command.

```bash
# Default (MySQL root user, no password)
bash init.sh

# With a password
DB_PASSWORD=your_password bash init.sh

# With a custom user
DB_USER=myuser DB_PASSWORD=mypass bash init.sh
```

The script will:
1. Create a `.venv` virtual environment and install dependencies
2. Create the `DB` database, load the schema, seed data, and triggers
3. Seed application users
4. Start the app at **http://127.0.0.1:5001**

> If the database already exists, steps 2–3 are skipped and the app starts directly.

---

## Manual Setup

If you prefer to run each step yourself:

### 1. Install Python dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Load the database

```bash
# Create schema (also creates the DB database)
mysql -u root -p < sql/schema.sql

# Load seed data
mysql -u root -p DB < sql/seed_data.sql

# Load triggers
mysql -u root -p DB < sql/triggers.sql
```

### 3. Seed application users

```bash
python seed_users.py
```

### 4. Run the application

```bash
python app.py
```

The app will be available at **http://127.0.0.1:5001**.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DB_USER` | `root` | MySQL username |
| `DB_PASSWORD` | *(empty)* | MySQL password |
| `DB_NAME` | `DB` | Database name |

---

## Project Structure

```
TransferDB/
├── app.py              # Flask entry point
├── db.py               # Database connection helpers
├── init.sh             # One-command setup & run script
├── requirements.txt
├── routes/             # Route blueprints (auth, manager, player, referee, dbmanager)
├── sql/
│   ├── schema.sql          # Table definitions
│   ├── schema_updates.sql  # Incremental schema changes
│   ├── seed_data.sql       # Sample football data
│   └── triggers.sql        # All business logic triggers
├── templates/          # Jinja2 HTML templates
└── tests/              # pytest test suite
```

---

## Running Tests

```bash
source .venv/bin/activate
pytest tests/
```
