import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings')
django.setup()

from firstapp.models import (
    User, PoliceStation, Location, Complaint, FIR, Case,
    Evidence, Accused, Alert, SOS, MissingPerson, LostFound, Landmark
)
from django.core.management import call_command

def sync_backup():
    print("--- Clearing existing cloud tables to prevent duplicate key conflicts ---")
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

    print("--- Loading full local dataset (1,235 records) from local_data.json ---")
    call_command('loaddata', 'local_data.json')
    print("--- Finished! Total records loaded: ---")
    print(f"Users: {User.objects.count()} (Citizens: {User.objects.filter(role='citizen').count()})")
    print(f"Stations: {PoliceStation.objects.count()}")
    print(f"Locations: {Location.objects.count()}")
    print(f"Complaints: {Complaint.objects.count()}")
    print(f"FIRs: {FIR.objects.count()}")
    print(f"Cases: {Case.objects.count()}")
    print(f"SOS: {SOS.objects.count()}")

if __name__ == '__main__':
    sync_backup()
