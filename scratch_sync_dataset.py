import os
import csv
import re
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings')
django.setup()

from firstapp.models import (
    User, PoliceStation, Location, Complaint, FIR, Case, Evidence, Accused, Alert, SOS, MissingPerson, LostFound
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, 'firstapp', 'templates', 'firstapp', 'dataset')
STATIONS_CSV = os.path.join(DATASET_DIR, 'madurai_police_stations (1).csv')
LOCATIONS_CSV = os.path.join(DATASET_DIR, 'madurai_locations.csv')

def clean_slug(name):
    # Remove words like Police Station, Police, etc. or simplify
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '_', s).strip('_')
    s = s.replace('police_station', '').replace('police_', '').replace('_police', '').strip('_')
    if not s:
        s = 'station'
    return s

def sync_data():
    print("--- 1. Clearing existing data ---")
    User.objects.all().delete()
    PoliceStation.objects.all().delete()
    Location.objects.all().delete()
    Complaint.objects.all().delete()
    FIR.objects.all().delete()
    Case.objects.all().delete()
    Evidence.objects.all().delete()
    Accused.objects.all().delete()
    Alert.objects.all().delete()
    SOS.objects.all().delete()
    MissingPerson.objects.all().delete()
    LostFound.objects.all().delete()
    print("Cleared all users, police stations, locations, complaints, FIRs, cases, alerts, sos.")

    # 2. Create System Admin
    admin_user = User.objects.create(
        name='System Administrator',
        email='admin@gmail.com',
        personal_email='admin@gmail.com',
        official_email='admin@tnpolice.gov.in',
        phone='0452-2539477',
        city='Madurai',
        state='Tamil Nadu',
        pincode='625001',
        password='admin123',
        role='admin',
        is_verified=True,
        approval_status='approved',
        created_at='2026-08-25 00:00:00'
    )
    print("Created Admin user: admin@gmail.com / admin123")

    # 3. Import Locations CSV
    print("\n--- 2. Importing Madurai Locations CSV ---")
    locations_created = 0
    with open(LOCATIONS_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            loc_name = row['Location'].strip()
            lat = row['Latitude'].strip()
            lon = row['Longitude'].strip()
            l_type = row.get('Type', 'Area').strip()
            
            # Avoid exact duplicate location names
            if not Location.objects.filter(name=loc_name).exists():
                Location.objects.create(
                    name=loc_name,
                    latitude=lat,
                    longitude=lon,
                    location_type=l_type
                )
                locations_created += 1
    print(f"Successfully imported {locations_created} Madurai locations into database.")

    # 4. Import Police Stations CSV and generate 4 verified officers for each station
    print("\n--- 3. Importing Police Stations CSV & Creating Officers ---")
    stations_created = 0
    officers_created = 0
    used_slugs = set()

    with open(STATIONS_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            st_name = row['StationName'].strip()
            address = row['Address'].strip()
            phone = row.get('PhoneNumber', '').strip() or '0452-2344101'
            lat = row['Latitude'].strip()
            lon = row['Longitude'].strip()
            st_type = row.get('Type', 'Police Station').strip()
            st_id = f"PS-{idx:03d}"

            station = PoliceStation.objects.create(
                station_id=st_id,
                name=st_name,
                station_type=st_type,
                district='Madurai',
                address=address,
                latitude=lat,
                longitude=lon,
                contact=phone
            )
            stations_created += 1

            # Determine email slug
            slug = clean_slug(st_name)
            if slug in used_slugs:
                slug = f"{slug}_{idx}"
            used_slugs.add(slug)

            # Define 4 officers per station:
            # 1. Inspector (Station In-Charge)
            # 2. Sub-Inspector (SI)
            # 3. Head Constable (HC)
            # 4. Constable (PC)
            roles_spec = [
                {
                    'rank': 'Inspector',
                    'role': 'inspector',
                    'name': f"Inspector {st_name}",
                    'email': f"ins.{slug}@tnpolice.gov.in",
                    'badge': f"TN-MDU-{idx:02d}-INS",
                },
                {
                    'rank': 'Sub-Inspector',
                    'role': 'officer',
                    'name': f"SI {st_name}",
                    'email': f"si.{slug}@tnpolice.gov.in",
                    'badge': f"TN-MDU-{idx:02d}-SI",
                },
                {
                    'rank': 'Head Constable',
                    'role': 'officer',
                    'name': f"Head Constable {st_name}",
                    'email': f"hc.{slug}@tnpolice.gov.in",
                    'badge': f"TN-MDU-{idx:02d}-HC",
                },
                {
                    'rank': 'Constable',
                    'role': 'officer',
                    'name': f"Constable {st_name}",
                    'email': f"pc.{slug}@tnpolice.gov.in",
                    'badge': f"TN-MDU-{idx:02d}-PC",
                }
            ]

            inspector_user = None
            for off in roles_spec:
                u = User.objects.create(
                    name=off['name'],
                    email=off['email'],
                    official_email=off['email'],
                    personal_email=f"{off['role']}.{slug}@gmail.com",
                    phone=phone.split(',')[0].strip(),
                    city='Madurai',
                    state='Tamil Nadu',
                    pincode='625001',
                    latitude=lat,
                    longitude=lon,
                    badge_number=off['badge'],
                    station=st_name,
                    station_id=st_id,
                    station_name=st_name,
                    rank=off['rank'],
                    password='password123',
                    role=off['role'],
                    is_verified=True,
                    approval_status='approved',
                    created_at='2026-08-25 00:00:00'
                )
                officers_created += 1
                if off['role'] == 'inspector':
                    inspector_user = u

            if inspector_user:
                station.incharge_inspector_id = str(inspector_user.id)
                station.incharge_inspector_name = inspector_user.name
                station.save()

    print(f"Successfully imported {stations_created} Police Stations and created {officers_created} verified Officers.")
    print("\n--- Summary of Created Police Stations & Inspector Logins ---")
    for s in PoliceStation.objects.all():
        ins = User.objects.filter(station_id=s.station_id, role='inspector').first()
        print(f"[{s.station_id}] {s.name} -> Inspector: {ins.name if ins else 'None'} | Login Email: {ins.official_email if ins else 'None'} (pwd: password123)")

if __name__ == '__main__':
    sync_data()
