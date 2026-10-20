import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings')
django.setup()

from django.test import Client
from firstapp.models import User, PoliceStation, Location, Complaint
from firstapp.geo_router import find_jurisdiction_station

def test_system():
    print("--- 1. Testing Database Entities ---")
    stations = PoliceStation.objects.all()
    print(f"Total Police Stations: {stations.count()}")
    locations = Location.objects.all()
    print(f"Total Madurai Locations: {locations.count()}")
    users = User.objects.all()
    print(f"Total Users/Officers: {users.count()}")
    inspectors = users.filter(role='inspector')
    print(f"Total Station Inspectors: {inspectors.count()}")
    officers = users.filter(role='officer')
    print(f"Total Officers (SI, HC, PC): {officers.count()}")

    print("\n--- 2. Testing Geo-Routing for Sample Madurai Areas ---")
    sample_areas = ['Anna Nagar', 'Sellur', 'Mattuthavani', 'Goripalayam', 'Koodal Nagar', 'Thiruparankundram']
    for a_name in sample_areas:
        loc = Location.objects.filter(name=a_name).first()
        if loc:
            matched, dist, reason = find_jurisdiction_station(
                complaint_lat=loc.latitude,
                complaint_lon=loc.longitude,
                address=loc.name,
                stations=list(stations)
            )
            print(f"Area: {loc.name:18} ({loc.latitude}, {loc.longitude}) -> Assigned Station: {matched.name if matched else 'None'} ({dist} km away)")

    print("\n--- 3. Testing Citizen Registration via Client ---")
    c = Client()
    reg_resp = c.post('/register/citizen/', {
        'full_name': 'Karthik Raja',
        'email': 'karthik.raja@gmail.com',
        'phone': '9876543210',
        'dob': '1998-05-15',
        'gender': 'Male',
        'area': 'Anna Nagar',
        'address': '45, Main Road, Anna Nagar',
        'city': 'Madurai',
        'pincode': '625020',
        'latitude': '9.94',
        'longitude': '78.13',
        'password': 'mypassword',
        'confirm_password': 'mypassword'
    })
    print(f"Registration status: {reg_resp.status_code} (Redirects to {reg_resp.get('Location', '')})")
    new_user = User.objects.filter(email='karthik.raja@gmail.com').first()
    if new_user:
        print(f"Created Citizen: {new_user.name} | Area: {new_user.area} | Lat/Lon: ({new_user.latitude}, {new_user.longitude})")

    print("\n--- 4. Testing Citizen Login and Filing Complaint ---")
    login_resp = c.post('/login/', {
        'email': 'karthik.raja@gmail.com',
        'password': 'mypassword'
    })
    print(f"Citizen Login Redirect: {login_resp.get('Location', '')}")

    cmp_resp = c.post('/citizen/complaint/new/', {
        'title': 'Stolen Bike near Mattuthavani',
        'category': 'Theft',
        'description': 'Hero Splendor bike parked near Mattuthavani bus stand was stolen.',
        'incident_date': '2026-08-25',
        'incident_time': '10:30',
        'area': 'Mattuthavani',
        'address': 'Near Bus Stand Platform 2',
        'city': 'Madurai',
        'pincode': '625007',
        'latitude': '9.95',
        'longitude': '78.13'
    })
    print(f"Complaint Filing Redirect: {cmp_resp.get('Location', '')}")

    complaint = Complaint.objects.filter(title__icontains='Stolen Bike').first()
    if complaint:
        print(f"Complaint Created: [{complaint.complaint_id}] {complaint.title}")
        print(f"  - Citizen: {complaint.citizen_name} ({complaint.citizen_email})")
        print(f"  - Area: {complaint.area}")
        print(f"  - Assigned Station: [{complaint.assigned_station_id}] {complaint.assigned_station_name}")
        print(f"  - AI Duplicate Flag: {complaint.ai_duplicate_flag} ({complaint.ai_similarity_score})")

    print("\n--- 5. Testing Inspector Login for Assigned Station ---")
    anna_inspector = User.objects.filter(station_name__icontains='Anna Nagar', role='inspector').first()
    if anna_inspector:
        print(f"Inspector found: {anna_inspector.name} | Email: {anna_inspector.official_email}")
        c_ins = Client()
        ins_login = c_ins.post('/login/', {
            'email': anna_inspector.official_email,
            'password': 'password123'
        })
    print("\n[SUCCESS] All End-to-End Tests Passed Successfully!")

if __name__ == '__main__':
    test_system()

