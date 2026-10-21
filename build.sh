#!/usr/bin/env bash
# Render build step: install deps, collect static files, migrate the database.
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Auto-seed initial stations and officers if database is empty
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings'); django.setup(); from firstapp.models import PoliceStation; import scratch_sync_dataset; (PoliceStation.objects.count() == 0) and scratch_sync_dataset.sync_data()"
