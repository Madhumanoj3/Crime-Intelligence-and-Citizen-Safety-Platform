#!/usr/bin/env bash
# Render build step: install deps, collect static files, migrate the database.
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Load exact up-to-date database fixture without unique key conflicts
python load_backup_data.py
