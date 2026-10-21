"""
Load the clean Madurai datasets into the database.

    python manage.py load_locations

Replaces every Location (areas) and Landmark row with the contents of
madurai_areas.csv and madurai_landmarks.csv. Police stations are not touched
because users and complaints already refer to them by station id.
Rebuild the CSVs with:  python ml/build_locations_dataset.py
"""
import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from firstapp.models import Landmark, Location

DATASET_DIR = os.path.join(settings.BASE_DIR, 'firstapp', 'templates', 'firstapp', 'dataset')


def read_rows(filename):
    with open(os.path.join(DATASET_DIR, filename), encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


class Command(BaseCommand):
    help = 'Replace Location and Landmark rows with the clean Madurai datasets.'

    @transaction.atomic
    def handle(self, *args, **options):
        areas = read_rows('madurai_areas.csv')
        landmarks = read_rows('madurai_landmarks.csv')

        Location.objects.all().delete()
        Location.objects.bulk_create([
            Location(name=r['Area'], latitude=r['Latitude'], longitude=r['Longitude'],
                     location_type=r['Type'] if r['Verified'] == 'Yes' else f"{r['Type']}, approx. location")
            for r in areas
        ])
        Landmark.objects.all().delete()
        Landmark.objects.bulk_create([
            Landmark(landmark_id=r['Landmark_ID'], name=r['Landmark'], landmark_type=r['Type'],
                     latitude=r['Latitude'], longitude=r['Longitude'], area=r['Area'],
                     distance_km=r['Distance_To_Area_km'], address=r['Address'])
            for r in landmarks
        ])
        self.stdout.write(self.style.SUCCESS(
            f'Loaded {len(areas)} areas ({sum(r['Verified'] == 'No' for r in areas)} with approximate coordinates) and {len(landmarks)} landmarks.'))
