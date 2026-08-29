import csv
import os
from datetime import datetime
# pyrefly: ignore [missing-import]
from django.conf import settings

BASE_DIR = settings.BASE_DIR

# CSV File Paths
USERS_CSV = os.path.join(BASE_DIR, 'users.csv')
COMPLAINTS_CSV = os.path.join(BASE_DIR, 'complaints.csv')
ALERTS_CSV = os.path.join(BASE_DIR, 'alerts.csv')
SOS_CSV = os.path.join(BASE_DIR, 'sos.csv')
MISSING_PERSONS_CSV = os.path.join(BASE_DIR, 'missing_persons.csv')
LOST_FOUND_CSV = os.path.join(BASE_DIR, 'lost_found.csv')
FIRS_CSV = os.path.join(BASE_DIR, 'firs.csv')
CASES_CSV = os.path.join(BASE_DIR, 'cases.csv')
EVIDENCE_CSV = os.path.join(BASE_DIR, 'evidence.csv')
ACCUSED_CSV = os.path.join(BASE_DIR, 'accused.csv')
POLICE_STATIONS_CSV = os.path.join(BASE_DIR, 'police_stations.csv')
FEEDBACK_CSV = os.path.join(BASE_DIR, 'feedback.csv')

# Field definitions
USERS_FIELDS = [
    'name', 'email', 'phone', 'dob', 'gender',
    'address', 'city', 'state', 'pincode',
    'badge_number', 'station', 'rank',
    'password', 'role', 'created_at'
]

COMPLAINTS_FIELDS = [
    'complaint_id', 'citizen_name', 'citizen_email', 'citizen_phone',
    'title', 'category', 'description', 'incident_date', 'incident_time',
    'address', 'street', 'city', 'pincode', 'latitude', 'longitude',
    'evidence', 'status', 'fir_status', 'case_status', 'created_at'
]

ALERTS_FIELDS = [
    'alert_id', 'title', 'description', 'area',
    'created_date', 'expiry_date', 'status', 'badge_class'
]

SOS_FIELDS = [
    'sos_id', 'citizen_name', 'citizen_email', 'citizen_phone',
    'time', 'location', 'latitude', 'longitude', 'status'
]

MISSING_PERSONS_FIELDS = [
    'person_id', 'name', 'age', 'gender', 'last_seen_date',
    'last_seen_location', 'description', 'photo', 'reported_by',
    'reported_date', 'status'
]

LOST_FOUND_FIELDS = [
    'item_id', 'item_type', 'name', 'category', 'description',
    'location', 'date', 'photo', 'reported_by', 'report_type', 'status'
]

FIRS_FIELDS = [
    'fir_id', 'complaint_id', 'section_of_law', 'fir_date',
    'description', 'status'
]

CASES_FIELDS = [
    'case_id', 'fir_id', 'complaint_id', 'assigned_officer',
    'officer_badge', 'status', 'start_date', 'end_date',
    'description', 'witnesses', 'accused_info'
]

EVIDENCE_FIELDS = [
    'evidence_id', 'complaint_id', 'file_name', 'file_type',
    'file_size', 'uploaded_date', 'added_by'
]

ACCUSED_FIELDS = [
    'accused_id', 'name', 'gender', 'phone', 'address',
    'criminal_status', 'marks', 'associated_cases'
]

POLICE_STATIONS_FIELDS = [
    'station_id', 'name', 'address', 'latitude', 'longitude', 'contact'
]

FEEDBACK_FIELDS = [
    'feedback_id', 'full_name', 'email', 'phone',
    'rating', 'products_used', 'feedback', 'submitted_at'
]


# Generic CSV Helpers
def read_csv(filepath, fields):
    init_all_csvs()
    data = []
    if not os.path.exists(filepath):
        return data
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(dict(row))
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return data


def append_csv(filepath, fields, item_dict):
    init_all_csvs()
    try:
        with open(filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writerow(item_dict)
        return True
    except Exception as e:
        print(f"Error appending to {filepath}: {e}")
        return False


def write_all_csv(filepath, fields, data_list):
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in data_list:
                writer.writerow(row)
        return True
    except Exception as e:
        print(f"Error writing to {filepath}: {e}")
        return False


# Initialization
def init_all_csvs():
    today_str = datetime.now().strftime('%Y-%m-%d')
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 1. Users CSV
    if not os.path.exists(USERS_CSV):
        users_seed = [
            {
                'name': 'Madhu Manoj',
                'email': 'madhumanoj094@gmail.com',
                'phone': '6374934366',
                'dob': '2007-03-03',
                'gender': 'male',
                'address': '12 South Gate Main Road',
                'city': 'Madurai',
                'state': 'Tamil Nadu',
                'pincode': '625001',
                'badge_number': '',
                'station': '',
                'rank': '',
                'password': 'password123',
                'role': 'citizen',
                'created_at': now_str
            },
            {
                'name': 'Karthik Raja',
                'email': 'karthik.raja@gmail.com',
                'phone': '+91 94431 23456',
                'dob': '1996-06-15',
                'gender': 'male',
                'address': '45 Anna Nagar 2nd Street',
                'city': 'Madurai',
                'state': 'Tamil Nadu',
                'pincode': '625020',
                'badge_number': '',
                'station': '',
                'rank': '',
                'password': 'password123',
                'role': 'citizen',
                'created_at': now_str
            },
            {
                'name': 'Meenakshi Sundaram',
                'email': 'meenakshi.sundaram@gmail.com',
                'phone': '+91 94862 78901',
                'dob': '1998-11-24',
                'gender': 'female',
                'address': '18 West Masi Street',
                'city': 'Madurai',
                'state': 'Tamil Nadu',
                'pincode': '625001',
                'badge_number': '',
                'station': '',
                'rank': '',
                'password': 'password123',
                'role': 'citizen',
                'created_at': now_str
            },
            {
                'name': 'SI Muthukumar',
                'email': 'muthukumar.si@tnpolice.gov.in',
                'phone': '+91 94981 12345',
                'dob': '1986-04-12',
                'gender': 'male',
                'address': 'Vilakkuthoon Police Station, South Masi Street',
                'city': 'Madurai',
                'state': 'Tamil Nadu',
                'pincode': '625001',
                'badge_number': 'TN-MD-101',
                'station': 'Vilakkuthoon PS',
                'rank': 'Sub Inspector',
                'password': 'police123',
                'role': 'police',
                'created_at': now_str
            },
            {
                'name': 'Inspector Soundarapandian',
                'email': 'soundar.pandian@tnpolice.gov.in',
                'phone': '+91 94981 67890',
                'dob': '1980-09-18',
                'gender': 'male',
                'address': 'Tallakulam Police Station, Alagarkoil Road',
                'city': 'Madurai',
                'state': 'Tamil Nadu',
                'pincode': '625002',
                'badge_number': 'TN-MD-205',
                'station': 'Tallakulam PS',
                'rank': 'Inspector',
                'password': 'policepassword',
                'role': 'police',
                'created_at': now_str
            }
        ]
        write_all_csv(USERS_CSV, USERS_FIELDS, users_seed)

    # 2. Complaints CSV
    if not os.path.exists(COMPLAINTS_CSV):
        complaints_seed = [
            {
                'complaint_id': 'CMP-001',
                'citizen_name': 'Madhu Manoj',
                'citizen_email': 'madhumanoj094@gmail.com',
                'citizen_phone': '6374934366',
                'title': 'Mobile Theft at Bus Stand',
                'category': 'Theft',
                'description': 'My mobile phone was stolen while I was waiting at the Periyar Bus Stand near West Veli Street, Madurai. The thief grabbed my Samsung Galaxy S23 and ran towards the market lane.',
                'incident_date': today_str,
                'incident_time': '14:30',
                'address': 'Periyar Bus Stand, West Veli Street',
                'street': 'West Veli Street',
                'city': 'Madurai',
                'pincode': '625001',
                'latitude': '9.9165',
                'longitude': '78.1128',
                'evidence': 'cctv_screenshot.jpg',
                'status': 'Pending',
                'fir_status': 'Not Filed',
                'case_status': 'Not Assigned',
                'created_at': now_str
            },
            {
                'complaint_id': 'CMP-002',
                'citizen_name': 'Kavitha Devi',
                'citizen_email': 'kavitha.devi@gmail.com',
                'citizen_phone': '+91 98432 11223',
                'title': 'Online Fraud - Bank Account',
                'category': 'Cybercrime',
                'description': 'Received a fake phishing call claiming to be bank verification and lost Rs. 25,000 through unauthorized UPI transfer.',
                'incident_date': today_str,
                'incident_time': '11:15',
                'address': 'K.K. Nagar 4th Street',
                'street': 'K.K. Nagar',
                'city': 'Madurai',
                'pincode': '625020',
                'latitude': '9.9320',
                'longitude': '78.1510',
                'evidence': 'screenshot_upi.png',
                'status': 'Under Review',
                'fir_status': 'Valid',
                'case_status': 'Assigned',
                'created_at': now_str
            },
            {
                'complaint_id': 'CMP-003',
                'citizen_name': 'Karthik Raja',
                'citizen_email': 'karthik.raja@gmail.com',
                'citizen_phone': '+91 94431 23456',
                'title': 'Road Accident Near Goripalayam',
                'category': 'Accident',
                'description': 'Reckless two-wheeler collision near Goripalayam signal. Minor injuries to pedestrian and damage to vehicle.',
                'incident_date': today_str,
                'incident_time': '09:45',
                'address': 'Goripalayam Signal Junction',
                'street': 'Goripalayam Main Road',
                'city': 'Madurai',
                'pincode': '625002',
                'latitude': '9.9298',
                'longitude': '78.1310',
                'evidence': 'accident_photo.jpg',
                'status': 'Resolved',
                'fir_status': 'Valid',
                'case_status': 'Closed',
                'created_at': now_str
            },
            {
                'complaint_id': 'CMP-004',
                'citizen_name': 'Deepa Lakshmi',
                'citizen_email': 'deepa.lakshmi@gmail.com',
                'citizen_phone': '+91 97890 33445',
                'title': 'Eve Teasing Complaint Near College',
                'category': 'Harassment',
                'description': 'Group of youths causing nuisance and passing vulgar comments outside Lady Doak College road during evening hours.',
                'incident_date': today_str,
                'incident_time': '17:30',
                'address': 'Lady Doak College Road, Tallakulam',
                'street': 'Tallakulam Road',
                'city': 'Madurai',
                'pincode': '625002',
                'latitude': '9.9392',
                'longitude': '78.1345',
                'evidence': 'witness_audio.mp3',
                'status': 'Resolved',
                'fir_status': 'Valid',
                'case_status': 'Closed',
                'created_at': now_str
            },
            {
                'complaint_id': 'CMP-005',
                'citizen_name': 'Madhu Manoj',
                'citizen_email': 'madhumanoj094@gmail.com',
                'citizen_phone': '6374934366',
                'title': 'Wallet Stolen in Market',
                'category': 'Theft',
                'description': 'Leather wallet with cash and driving license lost/stolen near Simmakkal market crowd.',
                'incident_date': today_str,
                'incident_time': '16:00',
                'address': 'Simmakkal Market Road',
                'street': 'Simmakkal',
                'city': 'Madurai',
                'pincode': '625001',
                'latitude': '9.9245',
                'longitude': '78.1220',
                'evidence': '',
                'status': 'Rejected',
                'fir_status': 'Not Filed',
                'case_status': 'Not Assigned',
                'created_at': now_str
            },
            {
                'complaint_id': 'CMP-006',
                'citizen_name': 'Saravanan',
                'citizen_email': 'saravanan.mdu@gmail.com',
                'citizen_phone': '+91 94421 55667',
                'title': 'Noise Complaint - Late Night Construction',
                'category': 'Other',
                'description': 'Heavy machinery operating past midnight in residential area causing extreme disturbance.',
                'incident_date': today_str,
                'incident_time': '23:30',
                'address': 'Anna Nagar 5th Cross',
                'street': 'Anna Nagar',
                'city': 'Madurai',
                'pincode': '625020',
                'latitude': '9.9248',
                'longitude': '78.1487',
                'evidence': '',
                'status': 'Resolved',
                'fir_status': 'Not Filed',
                'case_status': 'Closed',
                'created_at': now_str
            },
            {
                'complaint_id': 'CMP-007',
                'citizen_name': 'Murugesan',
                'citizen_email': 'murugesan.mdu@gmail.com',
                'citizen_phone': '+91 98421 77889',
                'title': 'Vehicle Damage Complaint',
                'category': 'Vandalism',
                'description': 'Car windshield broken intentionally while parked in front of house overnight.',
                'incident_date': today_str,
                'incident_time': '02:00',
                'address': 'Sellur Main Road',
                'street': 'Sellur',
                'city': 'Madurai',
                'pincode': '625002',
                'latitude': '9.9410',
                'longitude': '78.1190',
                'evidence': 'windshield_photo.jpg',
                'status': 'Under Review',
                'fir_status': 'Pending',
                'case_status': 'Assigned',
                'created_at': now_str
            },
            {
                'complaint_id': 'CMP-008',
                'citizen_name': 'Anbarasan',
                'citizen_email': 'anbarasan.tn@gmail.com',
                'citizen_phone': '+91 94890 99112',
                'title': 'Fake UPI Payment Received at Shop',
                'category': 'Fraud',
                'description': 'Customer showed spoofed payment screenshot and took goods worth Rs. 4,500 without payment.',
                'incident_date': today_str,
                'incident_time': '13:10',
                'address': 'South Masi Street, Madurai',
                'street': 'South Masi Street',
                'city': 'Madurai',
                'pincode': '625001',
                'latitude': '9.9160',
                'longitude': '78.1210',
                'evidence': 'shop_cctv.mp4',
                'status': 'Resolved',
                'fir_status': 'Valid',
                'case_status': 'Closed',
                'created_at': now_str
            }
        ]
        write_all_csv(COMPLAINTS_CSV, COMPLAINTS_FIELDS, complaints_seed)

    # 3. Alerts CSV
    if not os.path.exists(ALERTS_CSV):
        alerts_seed = [
            {
                'alert_id': 'ALT-001',
                'title': 'Heavy Traffic Near Bus Stand',
                'description': 'Heavy traffic congestion reported near the Mattuthavani MGR Bus Stand. Expect delays of 30-45 minutes.',
                'area': 'Mattuthavani MGR Bus Stand, Madurai',
                'created_date': today_str,
                'expiry_date': 'Active 48h',
                'status': 'Active',
                'badge_class': 'badge-warning'
            },
            {
                'alert_id': 'ALT-002',
                'title': 'Road Accident Reported',
                'description': 'A road accident has been reported on NH-44 near the Kappalur toll plaza. Emergency services and traffic police are on the way.',
                'area': 'NH-44 Kappalur Toll Plaza, Madurai',
                'created_date': today_str,
                'expiry_date': 'Active 24h',
                'status': 'Urgent',
                'badge_class': 'badge-danger'
            },
            {
                'alert_id': 'ALT-003',
                'title': 'Suspicious Activity Reported',
                'description': 'Suspicious activity reported in the Anna Nagar residential area during nighttime. Residents are advised to stay alert.',
                'area': 'Anna Nagar Residential, Madurai',
                'created_date': today_str,
                'expiry_date': 'Active 72h',
                'status': 'Active',
                'badge_class': 'badge-warning'
            },
            {
                'alert_id': 'ALT-004',
                'title': 'Weather Warning',
                'description': 'Heavy rainfall expected in Madurai region for the next 48 hours. Avoid low-lying areas and stay indoors if possible.',
                'area': 'Madurai District',
                'created_date': today_str,
                'expiry_date': 'Expired',
                'status': 'Expired',
                'badge_class': 'badge-pending'
            },
            {
                'alert_id': 'ALT-005',
                'title': 'Road Construction Notice',
                'description': 'Road construction and drainage work on South Veli Street will continue for the next 2 weeks. Use alternate routes.',
                'area': 'South Veli Street, Madurai',
                'created_date': 'Previous Notice',
                'expiry_date': 'Expired',
                'status': 'Expired',
                'badge_class': 'badge-pending'
            }
        ]
        write_all_csv(ALERTS_CSV, ALERTS_FIELDS, alerts_seed)

    # 4. SOS CSV
    if not os.path.exists(SOS_CSV):
        sos_seed = [
            {
                'sos_id': 'SOS-001',
                'citizen_name': 'Meenakshi Sundaram',
                'citizen_email': 'meenakshi.sundaram@email.com',
                'citizen_phone': '+91 94862 78901',
                'time': f"{today_str} 14:10",
                'location': 'Anna Nagar, Madurai',
                'latitude': '9.9248',
                'longitude': '78.1487',
                'status': 'Active'
            },
            {
                'sos_id': 'SOS-002',
                'citizen_name': 'Karthik Raja',
                'citizen_email': 'karthik.raja@email.com',
                'citizen_phone': '+91 94431 23456',
                'time': f"{today_str} 13:00 (1 hr ago)",
                'location': 'Periyar Bus Stand, Madurai',
                'latitude': '9.9165',
                'longitude': '78.1128',
                'status': 'Active'
            },
            {
                'sos_id': 'SOS-003',
                'citizen_name': 'Saravanan',
                'citizen_email': 'saravanan.mdu@email.com',
                'citizen_phone': '+91 94421 55667',
                'time': f"{today_str} (Yesterday)",
                'location': 'Goripalayam, Madurai',
                'latitude': '9.9298',
                'longitude': '78.1310',
                'status': 'Resolved'
            },
            {
                'sos_id': 'SOS-004',
                'citizen_name': 'Anbarasan',
                'citizen_email': 'anbarasan.tn@email.com',
                'citizen_phone': '+91 94890 99112',
                'time': f"{today_str} (2 days ago)",
                'location': 'Teppakulam, Madurai',
                'latitude': '9.9123',
                'longitude': '78.1456',
                'status': 'Resolved'
            }
        ]
        write_all_csv(SOS_CSV, SOS_FIELDS, sos_seed)

    # 5. Missing Persons CSV
    if not os.path.exists(MISSING_PERSONS_CSV):
        missing_seed = [
            {
                'person_id': 'MIS-001',
                'name': 'Murugesan',
                'age': '25',
                'gender': 'Male',
                'last_seen_date': today_str,
                'last_seen_location': 'Railway Station, Madurai',
                'description': 'Wearing blue shirt and black pants, height 5ft 8in.',
                'photo': '',
                'reported_by': 'Madhu Manoj',
                'reported_date': today_str,
                'status': 'Missing'
            },
            {
                'person_id': 'MIS-002',
                'name': 'Kavitha Selvam',
                'age': '19',
                'gender': 'Female',
                'last_seen_date': today_str,
                'last_seen_location': 'Mattuthavani Bus Stand, Madurai',
                'description': 'Wearing yellow churidar, carrying green backpack.',
                'photo': '',
                'reported_by': 'Selvam',
                'reported_date': today_str,
                'status': 'Missing'
            },
            {
                'person_id': 'MIS-003',
                'name': 'Sundaram Pillai',
                'age': '60',
                'gender': 'Male',
                'last_seen_date': today_str,
                'last_seen_location': 'Meenakshi Amman Temple Area, Madurai',
                'description': 'Elderly man with white veshti, speaks Tamil only.',
                'photo': '',
                'reported_by': 'Meenakshi Sundaram',
                'reported_date': today_str,
                'status': 'Found'
            }
        ]
        write_all_csv(MISSING_PERSONS_CSV, MISSING_PERSONS_FIELDS, missing_seed)

    # 6. Lost & Found CSV
    if not os.path.exists(LOST_FOUND_CSV):
        lost_found_seed = [
            {
                'item_id': 'LF-001',
                'item_type': 'electronics',
                'name': '📱 Samsung Phone',
                'category': 'Electronics',
                'description': 'Samsung Galaxy S23, black color with transparent case.',
                'location': 'Vishaal de Mal, Madurai',
                'date': today_str,
                'photo': '',
                'reported_by': 'Madhu Manoj',
                'report_type': 'lost',
                'status': 'Lost'
            },
            {
                'item_id': 'LF-002',
                'item_type': 'other',
                'name': '👜 Brown Leather Wallet',
                'category': 'Other',
                'description': 'Wildhorn brown leather wallet with cards and cash.',
                'location': 'Simmakkal, Madurai',
                'date': today_str,
                'photo': '',
                'reported_by': 'Shopkeeper Selvam',
                'report_type': 'found',
                'status': 'Found'
            },
            {
                'item_id': 'LF-003',
                'item_type': 'documents',
                'name': '📄 Aadhaar Card',
                'category': 'Documents',
                'description': 'Aadhaar card laminated copy in the name of K. Raja.',
                'location': 'Periyar Bus Stand, Madurai',
                'date': today_str,
                'photo': '',
                'reported_by': 'Karthik Raja',
                'report_type': 'lost',
                'status': 'Lost'
            },
            {
                'item_id': 'LF-004',
                'item_type': 'other',
                'name': '🔑 Car Keys (Maruti)',
                'category': 'Other',
                'description': 'Maruti Suzuki key with blue keychain.',
                'location': 'Railway Station, Madurai',
                'date': today_str,
                'photo': '',
                'reported_by': 'Auto Driver Murugan',
                'report_type': 'found',
                'status': 'Found'
            },
            {
                'item_id': 'LF-005',
                'item_type': 'jewelry',
                'name': '💍 Gold Ring',
                'category': 'Jewelry',
                'description': '22K gold ring with floral design, approx 4 grams.',
                'location': 'South Masi Street, Madurai',
                'date': today_str,
                'photo': '',
                'reported_by': 'Deepa Lakshmi',
                'report_type': 'lost',
                'status': 'Lost'
            },
            {
                'item_id': 'LF-006',
                'item_type': 'bag',
                'name': '🎒 Blue Backpack',
                'category': 'Bag/Luggage',
                'description': 'American Tourister blue bag containing notebooks.',
                'location': 'Goripalayam, Madurai',
                'date': today_str,
                'photo': '',
                'reported_by': 'Traffic Constable',
                'report_type': 'found',
                'status': 'Found'
            }
        ]
        write_all_csv(LOST_FOUND_CSV, LOST_FOUND_FIELDS, lost_found_seed)

    # 7. FIRs CSV
    if not os.path.exists(FIRS_CSV):
        firs_seed = [
            {
                'fir_id': 'FIR-001',
                'complaint_id': 'CMP-001',
                'section_of_law': 'IPC Section 379 (Theft)',
                'fir_date': today_str,
                'description': 'Mobile theft at Periyar Bus Stand filed under Section 379 IPC.',
                'status': 'Valid'
            },
            {
                'fir_id': 'FIR-002',
                'complaint_id': 'CMP-002',
                'section_of_law': 'IT Act Section 66C & 66D',
                'fir_date': today_str,
                'description': 'Phishing and cyber fraud unauthorized account transfer.',
                'status': 'Valid'
            },
            {
                'fir_id': 'FIR-003',
                'complaint_id': 'CMP-003',
                'section_of_law': 'IPC Section 279 (Rash Driving)',
                'fir_date': today_str,
                'description': 'Rash driving leading to road accident at Goripalayam.',
                'status': 'Valid'
            },
            {
                'fir_id': 'FIR-004',
                'complaint_id': 'CMP-004',
                'section_of_law': 'IPC Section 354 (Harassment)',
                'fir_date': today_str,
                'description': 'Public nuisance and harassment of women at Tallakulam.',
                'status': 'Pending Review'
            }
        ]
        write_all_csv(FIRS_CSV, FIRS_FIELDS, firs_seed)

    # 8. Cases CSV
    if not os.path.exists(CASES_CSV):
        cases_seed = [
            {
                'case_id': 'CASE-001',
                'fir_id': 'FIR-001',
                'complaint_id': 'CMP-001',
                'assigned_officer': 'SI Muthukumar',
                'officer_badge': 'TN-MD-101',
                'status': 'Under Investigation',
                'start_date': today_str,
                'end_date': '—',
                'description': 'The investigation is ongoing. CCTV footage from nearby cameras has been collected. Witnesses have been interviewed. The suspect has been identified based on CCTV evidence and is being tracked.',
                'witnesses': 'CCTV Footage — Bus Stand Camera #3 | Witness Statement — Mr. Selvam (Shopkeeper, Simmakkal, Madurai)',
                'accused_info': 'Suspect identified — Male, approx. 25-30 years'
            },
            {
                'case_id': 'CASE-002',
                'fir_id': 'FIR-002',
                'complaint_id': 'CMP-002',
                'assigned_officer': 'Inspector Soundarapandian',
                'officer_badge': 'TN-MD-205',
                'status': 'Open',
                'start_date': today_str,
                'end_date': '—',
                'description': 'Cybercrime investigation in coordination with bank nodal officers to freeze recipient account.',
                'witnesses': 'Bank transaction logs | Call records',
                'accused_info': 'Account holder traced to remote location'
            },
            {
                'case_id': 'CASE-003',
                'fir_id': 'FIR-003',
                'complaint_id': 'CMP-003',
                'assigned_officer': 'SI Muthukumar',
                'officer_badge': 'TN-MD-101',
                'status': 'Closed',
                'start_date': today_str,
                'end_date': today_str,
                'description': 'Accident settled through mutual agreement and fine imposed under Motor Vehicles Act.',
                'witnesses': 'Traffic footage | Vehicle inspection report',
                'accused_info': 'Rider penalized'
            }
        ]
        write_all_csv(CASES_CSV, CASES_FIELDS, cases_seed)

    # 9. Evidence CSV
    if not os.path.exists(EVIDENCE_CSV):
        evidence_seed = [
            {
                'evidence_id': 'EVD-001',
                'complaint_id': 'CMP-001',
                'file_name': 'cctv_screenshot.jpg',
                'file_type': 'Image',
                'file_size': '245 KB',
                'uploaded_date': today_str,
                'added_by': 'Madhu Manoj (Citizen)'
            },
            {
                'evidence_id': 'EVD-002',
                'complaint_id': 'CMP-001',
                'file_name': 'cctv_footage.mp4',
                'file_type': 'Video',
                'file_size': '15.2 MB',
                'uploaded_date': today_str,
                'added_by': 'SI Muthukumar (Police)'
            },
            {
                'evidence_id': 'EVD-003',
                'complaint_id': 'CMP-002',
                'file_name': 'bank_statement.pdf',
                'file_type': 'PDF',
                'file_size': '1.1 MB',
                'uploaded_date': today_str,
                'added_by': 'Kavitha Devi (Citizen)'
            },
            {
                'evidence_id': 'EVD-004',
                'complaint_id': 'CMP-002',
                'file_name': 'screenshot_upi.png',
                'file_type': 'Image',
                'file_size': '380 KB',
                'uploaded_date': today_str,
                'added_by': 'Kavitha Devi (Citizen)'
            },
            {
                'evidence_id': 'EVD-005',
                'complaint_id': 'CMP-003',
                'file_name': 'accident_photo.jpg',
                'file_type': 'Image',
                'file_size': '890 KB',
                'uploaded_date': today_str,
                'added_by': 'Karthik Raja (Citizen)'
            },
            {
                'evidence_id': 'EVD-006',
                'complaint_id': 'CMP-004',
                'file_name': 'witness_statement.pdf',
                'file_type': 'PDF',
                'file_size': '520 KB',
                'uploaded_date': today_str,
                'added_by': 'Inspector Soundarapandian (Police)'
            }
        ]
        write_all_csv(EVIDENCE_CSV, EVIDENCE_FIELDS, evidence_seed)

    # 10. Accused CSV
    if not os.path.exists(ACCUSED_CSV):
        accused_seed = [
            {
                'accused_id': 'ACC-001',
                'name': 'Pandiarajan',
                'gender': 'Male',
                'phone': '+91 98421 11223',
                'address': 'Sellur, Madurai, Tamil Nadu',
                'criminal_status': 'Repeat Offender',
                'marks': 'Scar on left hand, tattoo on right arm',
                'associated_cases': 'CMP-001, CASE-001 | CMP-015, CASE-008'
            },
            {
                'accused_id': 'ACC-002',
                'name': 'Veeramani',
                'gender': 'Male',
                'phone': '+91 97890 22334',
                'address': 'Keelavasal, Madurai, Tamil Nadu',
                'criminal_status': 'First Offence',
                'marks': 'Burn mark on left shoulder',
                'associated_cases': 'CMP-004, CASE-003'
            },
            {
                'accused_id': 'ACC-003',
                'name': 'Maruthupandian',
                'gender': 'Male',
                'phone': '+91 94432 33445',
                'address': 'Anuppanadi, Madurai, Tamil Nadu',
                'criminal_status': 'Repeat Offender',
                'marks': 'Mole on right cheek',
                'associated_cases': 'CMP-007, CASE-005'
            }
        ]
        write_all_csv(ACCUSED_CSV, ACCUSED_FIELDS, accused_seed)

    # 11. Police Stations CSV
    if not os.path.exists(POLICE_STATIONS_CSV):
        stations_seed = [
            {
                'station_id': 'PS-001',
                'name': 'Vilakkuthoon Police Station',
                'address': 'South Masi Street, Madurai',
                'latitude': '9.9165',
                'longitude': '78.1215',
                'contact': '0452-2342100'
            },
            {
                'station_id': 'PS-002',
                'name': 'Tallakulam Police Station',
                'address': 'Alagarkoil Road, Tallakulam, Madurai',
                'latitude': '9.9392',
                'longitude': '78.1345',
                'contact': '0452-2531800'
            },
            {
                'station_id': 'PS-003',
                'name': 'Mattuthavani Police Station',
                'address': 'MGR Bus Terminus, Mattuthavani, Madurai',
                'latitude': '9.9542',
                'longitude': '78.1632',
                'contact': '0452-2582300'
            },
            {
                'station_id': 'PS-004',
                'name': 'Anna Nagar Police Station',
                'address': 'Kuruvikaran Salai, Anna Nagar, Madurai',
                'latitude': '9.9248',
                'longitude': '78.1487',
                'contact': '0452-2521400'
            }
        ]
        write_all_csv(POLICE_STATIONS_CSV, POLICE_STATIONS_FIELDS, stations_seed)

    # 12. Feedback CSV
    if not os.path.exists(FEEDBACK_CSV):
        write_all_csv(FEEDBACK_CSV, FEEDBACK_FIELDS, [])
