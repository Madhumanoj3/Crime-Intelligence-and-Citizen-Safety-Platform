import os
import sys

# Support passing a remote database URL directly from command line:
# python load_backup_data.py --database-url="postgres://..."
for arg in sys.argv[1:]:
    if arg.startswith('--database-url='):
        os.environ['DATABASE_URL'] = arg.split('=', 1)[1].strip('"\'')
    elif arg.startswith('--db='):
        os.environ['DATABASE_URL'] = arg.split('=', 1)[1].strip('"\'')

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings')
django.setup()

from django.conf import settings
from django.core.management import call_command
from firstapp.models import (
    User, PoliceStation, Location, Complaint, FIR, Case,
    Evidence, Accused, Alert, SOS, MissingPerson, LostFound, Landmark, Feedback
)

def sync_backup():
    db_conf = settings.DATABASES['default']
    target_info = db_conf.get('HOST', 'localhost')
    if os.getenv('DATABASE_URL'):
        target_info = f"Remote Cloud Database ({os.getenv('DATABASE_URL').split('@')[-1].split('/')[0]})"
    print(f"--- Target Database: {target_info} ---")

    print("--- Ensuring database migrations are applied ---")
    call_command('migrate', interactive=False)

    print("--- Clearing existing tables to prevent duplicate key conflicts ---")
    Feedback.objects.all().delete()
    Evidence.objects.all().delete()
    Case.objects.all().delete()
    FIR.objects.all().delete()
    Complaint.objects.all().delete()
    SOS.objects.all().delete()
    Alert.objects.all().delete()
    MissingPerson.objects.all().delete()
    LostFound.objects.all().delete()
    Accused.objects.all().delete()
    Landmark.objects.all().delete()
    PoliceStation.objects.all().delete()
    Location.objects.all().delete()
    User.objects.all().delete()

    print("--- Loading full dataset from local_data.json ---")
    call_command('loaddata', 'local_data.json')
    print("--- Finished! Total records loaded into database: ---")
    print(f"Users: {User.objects.count()} (Citizens: {User.objects.filter(role='citizen').count()})")
    print(f"Stations: {PoliceStation.objects.count()}")
    print(f"Locations: {Location.objects.count()}")
    print(f"Landmarks: {Landmark.objects.count()}")
    print(f"Complaints: {Complaint.objects.count()}")
    print(f"FIRs: {FIR.objects.count()}")
    print(f"Cases: {Case.objects.count()}")
    print(f"SOS: {SOS.objects.count()}")
    print(f"Missing Persons: {MissingPerson.objects.count()}")
    print(f"Lost & Found: {LostFound.objects.count()}")

if __name__ == '__main__':
    sync_backup()
