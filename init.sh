#!/usr/bin/env bash

set -euo pipefail

# Allow overrides from environment while keeping sensible defaults.
export DB_USER="${DB_USER:-root}"
export DB_PASSWORD="${DB_PASSWORD:-}"
export DB_NAME="${DB_NAME:-DB}"

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "[1/6] Preparing virtual environment..."
if [[ ! -d .venv ]]; then
	python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "[2/6] Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

if ! command -v mysql >/dev/null 2>&1; then
	echo "Error: mysql CLI not found. Install MySQL client and retry."
	exit 1
fi

# Build mysql auth args safely for both empty and non-empty passwords.
MYSQL_AUTH=(-u "$DB_USER")
if [[ -n "$DB_PASSWORD" ]]; then
	MYSQL_AUTH+=("-p$DB_PASSWORD")
fi

echo "[3/6] Checking database state..."
DB_EXISTS="$(mysql "${MYSQL_AUTH[@]}" -N -B -e "SHOW DATABASES LIKE '$DB_NAME';" || true)"

if [[ "$DB_EXISTS" == "$DB_NAME" ]]; then
	echo "Database '$DB_NAME' already exists. Skipping schema, seed data, triggers, and user seeding."
else
	echo "[4/6] Creating schema..."
	mysql "${MYSQL_AUTH[@]}" < sql/schema.sql

	echo "[5/6] Seeding base data..."
	perl -pe "s/, 'Completed'\\);/\\);/g" sql/seed_data.sql | mysql "${MYSQL_AUTH[@]}" "$DB_NAME"

	echo "[6/6] Creating triggers and seeding app users..."
	mysql "${MYSQL_AUTH[@]}" "$DB_NAME" < sql/triggers.sql
	python seed_users.py
fi

echo "Starting app on http://127.0.0.1:5001"
python app.py