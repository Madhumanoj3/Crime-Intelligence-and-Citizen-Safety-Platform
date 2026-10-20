# pyrefly: ignore [missing-import]
from django.db import models


class User(models.Model):
    ROLE_CHOICES = [
        ('citizen', 'Citizen'),
        ('inspector', 'Inspector (Station In-Charge)'),
        ('officer', 'Police Officer'),
        ('admin', 'Admin'),
        ('police', 'Police Applicant / Personnel'),
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    personal_email = models.CharField(max_length=100, blank=True)
    official_email = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    dob = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    area = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    latitude = models.CharField(max_length=20, blank=True)
    longitude = models.CharField(max_length=20, blank=True)
    badge_number = models.CharField(max_length=30, blank=True)
    station = models.CharField(max_length=100, blank=True)
    station_id = models.CharField(max_length=30, blank=True)
    station_name = models.CharField(max_length=200, blank=True)
    rank = models.CharField(max_length=50, blank=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    is_verified = models.BooleanField(default=True)
    approval_status = models.CharField(max_length=30, default='approved')
    created_at = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f"{self.name} ({self.role})"


class PoliceStation(models.Model):
    station_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    station_type = models.CharField(max_length=50, blank=True, default='Police Station')
    district = models.CharField(max_length=100, blank=True, default='Madurai')
    address = models.TextField()
    latitude = models.CharField(max_length=20)
    longitude = models.CharField(max_length=20)
    contact = models.CharField(max_length=50, blank=True)
    incharge_inspector_id = models.CharField(max_length=50, blank=True)
    incharge_inspector_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.station_id} - {self.name}"


class Location(models.Model):
    name = models.CharField(max_length=200, unique=True)
    latitude = models.CharField(max_length=20)
    longitude = models.CharField(max_length=20)
    location_type = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"


class Complaint(models.Model):
    complaint_id = models.CharField(max_length=20, unique=True)
    citizen_name = models.CharField(max_length=100)
    citizen_email = models.EmailField()
    citizen_phone = models.CharField(max_length=20, blank=True)
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50)
    description = models.TextField()
    incident_date = models.CharField(max_length=20)
    incident_time = models.CharField(max_length=10)
    address = models.TextField(blank=True)
    area = models.CharField(max_length=100, blank=True)
    street = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50, blank=True)
    district = models.CharField(max_length=50, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    latitude = models.CharField(max_length=20, blank=True)
    longitude = models.CharField(max_length=20, blank=True)
    evidence = models.CharField(max_length=200, blank=True)

    # Station & Officer Assignment (Hierarchy)
    assigned_station_id = models.CharField(max_length=30, blank=True)
    assigned_station_name = models.CharField(max_length=200, blank=True)
    assigned_officer_id = models.CharField(max_length=254, blank=True)  # stores the officer's email
    assigned_officer_name = models.CharField(max_length=100, blank=True)
    assigned_by_inspector = models.CharField(max_length=100, blank=True)
    assigned_date = models.CharField(max_length=30, blank=True)

    # Status tracking
    status = models.CharField(max_length=40, default='Pending Review')
    fir_status = models.CharField(max_length=30, default='Not Filed')
    case_status = models.CharField(max_length=30, default='Not Assigned')

    # AI Duplicate Detection fields
    ai_duplicate_flag = models.CharField(max_length=30, default='Unique')
    ai_similarity_score = models.CharField(max_length=20, blank=True)
    ai_matched_complaint_id = models.CharField(max_length=30, blank=True)
    ai_matched_title = models.CharField(max_length=200, blank=True)

    # AI Priority Prediction (decision support only; Inspector makes the final decision)
    ai_priority = models.CharField(max_length=10, blank=True, default='')  # Low / Medium / High, '' = not predicted
    ai_priority_confidence = models.CharField(max_length=10, blank=True, default='')  # e.g. '87.5%'

    # Investigation & Rejection notes
    investigation_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f"{self.complaint_id} - {self.title} ({self.status})"


class Alert(models.Model):
    alert_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    area = models.CharField(max_length=200)
    created_date = models.CharField(max_length=30)
    expiry_date = models.CharField(max_length=30)
    status = models.CharField(max_length=20)
    badge_class = models.CharField(max_length=30)

    def __str__(self):
        return self.alert_id


class SOS(models.Model):
    sos_id = models.CharField(max_length=20, unique=True)
    citizen_name = models.CharField(max_length=100)
    citizen_email = models.EmailField()
    citizen_phone = models.CharField(max_length=20, blank=True)
    time = models.CharField(max_length=30)
    location = models.CharField(max_length=200)
    latitude = models.CharField(max_length=20, blank=True)
    longitude = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, default='Active')
    description = models.TextField(blank=True, default='')
    assigned_station_id = models.CharField(max_length=20, blank=True, default='')
    assigned_station_name = models.CharField(max_length=200, blank=True, default='')
    distance_km = models.CharField(max_length=20, blank=True, default='')

    def __str__(self):
        return self.sos_id


class MissingPerson(models.Model):
    person_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    age = models.CharField(max_length=10)
    gender = models.CharField(max_length=20)
    last_seen_date = models.CharField(max_length=20)
    last_seen_location = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    photo = models.CharField(max_length=200, blank=True)
    reported_by = models.CharField(max_length=100)
    reported_date = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default='Missing')

    def __str__(self):
        return self.person_id


class LostFound(models.Model):
    item_id = models.CharField(max_length=20, unique=True)
    item_type = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200)
    date = models.CharField(max_length=20)
    photo = models.CharField(max_length=200, blank=True)
    reported_by = models.CharField(max_length=100)
    report_type = models.CharField(max_length=10)
    status = models.CharField(max_length=20)

    def __str__(self):
        return self.item_id


class FIR(models.Model):
    fir_id = models.CharField(max_length=20, unique=True)
    complaint_id = models.CharField(max_length=20)
    station_id = models.CharField(max_length=30, blank=True)
    station_name = models.CharField(max_length=200, blank=True)
    investigating_officer = models.CharField(max_length=100, blank=True)
    officer_badge = models.CharField(max_length=30, blank=True)
    section_of_law = models.CharField(max_length=200)
    fir_date = models.CharField(max_length=20)
    description = models.TextField()
    status = models.CharField(max_length=30)

    def __str__(self):
        return self.fir_id


class Case(models.Model):
    case_id = models.CharField(max_length=20, unique=True)
    fir_id = models.CharField(max_length=20)
    complaint_id = models.CharField(max_length=20)
    station_id = models.CharField(max_length=30, blank=True)
    assigned_officer = models.CharField(max_length=100)
    officer_badge = models.CharField(max_length=30)
    status = models.CharField(max_length=30)
    start_date = models.CharField(max_length=20)
    end_date = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    witnesses = models.TextField(blank=True)
    accused_info = models.TextField(blank=True)
    last_update = models.CharField(max_length=30, blank=True)
    investigation_summary = models.TextField(blank=True)

    def __str__(self):
        return self.case_id


class Evidence(models.Model):
    evidence_id = models.CharField(max_length=20, unique=True)
    complaint_id = models.CharField(max_length=20)
    file_name = models.CharField(max_length=200)
    file_type = models.CharField(max_length=20)
    file_size = models.CharField(max_length=20)
    uploaded_date = models.CharField(max_length=20)
    added_by = models.CharField(max_length=100)

    def __str__(self):
        return self.evidence_id


class Accused(models.Model):
    accused_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=20)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    criminal_status = models.CharField(max_length=50)
    marks = models.TextField(blank=True)
    associated_cases = models.TextField(blank=True)

    def __str__(self):
        return self.accused_id


class Feedback(models.Model):
    feedback_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    rating = models.CharField(max_length=5)
    products_used = models.CharField(max_length=200, blank=True)
    feedback = models.TextField(blank=True)
    submitted_at = models.CharField(max_length=30)

    def __str__(self):
        return self.feedback_id
