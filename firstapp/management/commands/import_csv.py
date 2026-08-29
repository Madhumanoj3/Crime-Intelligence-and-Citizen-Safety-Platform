import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from firstapp.models import (
    User, Complaint, Alert, SOS, MissingPerson,
    LostFound, FIR, Case, Evidence, Accused, PoliceStation, Feedback
)

BASE_DIR = settings.BASE_DIR


def load(filepath, model, unique_field):
    if not os.path.exists(filepath):
        print(f"  Skipped (not found): {filepath}")
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    count = 0
    for row in rows:
        row = {k: v for k, v in row.items() if k}  # strip empty keys
        uid = row.get(unique_field)
        if uid and not model.objects.filter(**{unique_field: uid}).exists():
            try:
                model.objects.create(**row)
                count += 1
            except Exception as e:
                print(f"  Error on {uid}: {e}")
    print(f"  Imported {count} rows into {model.__name__}")


class Command(BaseCommand):
    help = 'Import all CSV data into PostgreSQL'

    def handle(self, *args, **kwargs):
        load(os.path.join(BASE_DIR, 'users.csv'), User, 'email')
        load(os.path.join(BASE_DIR, 'complaints.csv'), Complaint, 'complaint_id')
        load(os.path.join(BASE_DIR, 'alerts.csv'), Alert, 'alert_id')
        load(os.path.join(BASE_DIR, 'sos.csv'), SOS, 'sos_id')
        load(os.path.join(BASE_DIR, 'missing_persons.csv'), MissingPerson, 'person_id')
        load(os.path.join(BASE_DIR, 'lost_found.csv'), LostFound, 'item_id')
        load(os.path.join(BASE_DIR, 'firs.csv'), FIR, 'fir_id')
        load(os.path.join(BASE_DIR, 'cases.csv'), Case, 'case_id')
        load(os.path.join(BASE_DIR, 'evidence.csv'), Evidence, 'evidence_id')
        load(os.path.join(BASE_DIR, 'accused.csv'), Accused, 'accused_id')
        load(os.path.join(BASE_DIR, 'police_stations.csv'), PoliceStation, 'station_id')
        load(os.path.join(BASE_DIR, 'feedback.csv'), Feedback, 'feedback_id')
        self.stdout.write(self.style.SUCCESS('CSV import complete!'))
