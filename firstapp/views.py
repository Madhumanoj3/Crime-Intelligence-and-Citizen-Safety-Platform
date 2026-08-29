from datetime import datetime
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Q

from .models import (
    User, Complaint, Alert, SOS, MissingPerson,
    LostFound, FIR, Case, Evidence, Accused, PoliceStation, Feedback, Location
)
from .ai_detector import check_duplicate_complaint
from .geo_router import find_jurisdiction_station


def get_current_user(request):
    """Retrieve logged-in user from session or fallback default."""
    return request.session.get('user') or {
        'name': 'Guest User',
        'email': 'guest@gmail.com',
        'phone': '9876543210',
        'city': 'Madurai',
        'state': 'Tamil Nadu',
        'role': 'citizen',
        'badge_number': '',
        'station': '',
        'station_id': '',
        'station_name': '',
        'rank': '',
        'area': 'Madurai Center',
        'latitude': '9.9252',
        'longitude': '78.1198',
    }


def _user_to_dict(u):
    return {
        'id': u.id,
        'name': u.name,
        'email': u.official_email or u.email,
        'personal_email': u.personal_email or u.email,
        'official_email': u.official_email,
        'phone': u.phone,
        'area': getattr(u, 'area', ''),
        'latitude': getattr(u, 'latitude', ''),
        'longitude': getattr(u, 'longitude', ''),
        'city': u.city,
        'state': u.state,
        'role': u.role,
        'badge_number': u.badge_number,
        'station': u.station,
        'station_id': u.station_id,
        'station_name': u.station_name,
        'rank': u.rank,
        'dob': u.dob,
        'gender': u.gender,
        'address': u.address,
        'pincode': u.pincode,
        'is_verified': u.is_verified,
        'approval_status': u.approval_status,
    }


def _complaint_to_dict(c):
    return {f.name: getattr(c, f.name) for f in c._meta.fields}


# ==============================================================================
# 1. PUBLIC & AUTH VIEWS
# ==============================================================================

def index(request):
    return render(request, 'firstapp/index.html')


def register(request):
    error = None
    locations = Location.objects.all().order_by('name')
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        dob = request.POST.get('dob', '').strip()
        gender = request.POST.get('gender', '').strip()
        address = request.POST.get('address', '').strip()
        area = request.POST.get('area', '').strip()
        city = request.POST.get('city', '').strip() or 'Madurai'
        state = request.POST.get('state', '').strip() or 'Tamil Nadu'
        pincode = request.POST.get('pincode', '').strip() or '625001'
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        # If area is selected, look up exact coordinates from Madurai locations
        if area and (not latitude or not longitude):
            loc_obj = Location.objects.filter(name__iexact=area).first()
            if loc_obj:
                latitude = loc_obj.latitude
                longitude = loc_obj.longitude

        if not email or not password or not full_name:
            error = "Please fill in all required fields."
        elif '@' not in email or '.' not in email:
            error = "Please enter a valid email address."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif User.objects.filter(Q(email=email) | Q(personal_email=email) | Q(official_email=email)).exists():
            error = "An account with this email already exists. Please login."
        else:
            User.objects.create(
                name=full_name, email=email, personal_email=email,
                phone=phone, dob=dob, gender=gender,
                address=address, area=area, city=city, state=state, pincode=pincode,
                latitude=latitude or '9.9252', longitude=longitude or '78.1198',
                password=password, role='citizen',
                is_verified=True, approval_status='approved',
                created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            return redirect('/login/?registered=citizen')

    return render(request, 'firstapp/register.html', {
        'active_tab': 'citizen',
        'error': error,
        'locations': locations
    })


def police_register(request):
    error = None
    locations = Location.objects.all().order_by('name')
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', '').strip()
        address = request.POST.get('address', '').strip()
        area = request.POST.get('area', '').strip()
        city = request.POST.get('city', '').strip() or 'Madurai'
        state = request.POST.get('state', '').strip() or 'Tamil Nadu'
        pincode = request.POST.get('pincode', '').strip() or '625001'
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if area and (not latitude or not longitude):
            loc_obj = Location.objects.filter(name__iexact=area).first()
            if loc_obj:
                latitude = loc_obj.latitude
                longitude = loc_obj.longitude

        if not email or not password or not full_name:
            error = "Please fill in all required fields."
        elif '@' not in email or '.' not in email:
            error = "Please enter a valid personal email address."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif User.objects.filter(Q(email=email) | Q(personal_email=email) | Q(official_email=email)).exists():
            error = "An account with this email already exists. Please login."
        else:
            # Police signs up with personal email; posting & official email will be assigned by Admin
            User.objects.create(
                name=full_name,
                email=email,
                personal_email=email,
                official_email='',
                phone=phone,
                gender=gender,
                address=address,
                area=area,
                city=city,
                state=state,
                pincode=pincode,
                latitude=latitude or '9.9252',
                longitude=longitude or '78.1198',
                password=password,
                role='police',
                badge_number='',
                station='',
                station_id='',
                station_name='',
                rank='',
                is_verified=False,
                approval_status='pending',
                created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            return redirect('/login/?registered=police_pending')

    return render(request, 'firstapp/police_register.html', {
        'active_tab': 'police',
        'error': error,
        'locations': locations
    })


def login_view(request):
    error = None
    success = None
    registered = request.GET.get('registered')
    if registered == 'citizen':
        success = "Citizen account created successfully! You can now log in."
    elif registered == 'police_pending':
        success = "Police registration submitted! Your account is pending Admin verification. The Administrator will assign your Station posting and official @tnpolice.gov.in credentials."
    elif registered == 'police':
        success = "Police account registered successfully! You can now log in."

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()

        if not email or not password:
            error = "Please enter both email and password."
        elif email == 'admin@gmail.com':
            if password == 'admin123':
                request.session['user'] = {
                    'name': 'System Administrator', 'email': 'admin@gmail.com',
                    'phone': '', 'city': 'Madurai', 'state': 'Tamil Nadu', 'role': 'admin'
                }
                return redirect('admin_dashboard')
            else:
                error = "Invalid administrator credentials."
        else:
            # Check user by official_email, primary email, or personal_email
            u = User.objects.filter(
                Q(email__iexact=email) | Q(official_email__iexact=email) | Q(personal_email__iexact=email),
                password=password
            ).first()

            if not u:
                error = "Invalid email or password. Please check your credentials."
            elif u.role in ['police', 'officer', 'inspector'] and (not u.is_verified or u.approval_status == 'pending'):
                error = "Your police account is pending verification and posting assignment by the Administrator. Please contact Department Admin."
            elif u.role == 'inspector':
                request.session['user'] = _user_to_dict(u)
                return redirect('inspector_dashboard')
            elif u.role in ['officer', 'police']:
                request.session['user'] = _user_to_dict(u)
                return redirect('officer_dashboard')
            elif u.role == 'citizen':
                request.session['user'] = _user_to_dict(u)
                return redirect('citizen_dashboard')
            else:
                request.session['user'] = _user_to_dict(u)
                return redirect('citizen_dashboard')

    return render(request, 'firstapp/login.html', {'error': error, 'success': success})


def logout_view(request):
    request.session.flush()
    return redirect('login')


# ==============================================================================
# 2. CITIZEN VIEWS (SUBMIT & TRACK COMPLAINTS)
# ==============================================================================

def citizen_dashboard(request):
    user = get_current_user(request)
    user_email = user.get('email', '').lower()
    user_personal = user.get('personal_email', '').lower()

    user_complaints = Complaint.objects.filter(
        Q(citizen_email__iexact=user_email) | Q(citizen_email__iexact=user_personal)
    )
    user_sos = SOS.objects.filter(
        Q(citizen_email__iexact=user_email) | Q(citizen_email__iexact=user_personal)
    )

    return render(request, 'firstapp/citizen_dashboard.html', {
        'current_user': user,
        'total_complaints': user_complaints.count(),
        'active_complaints': user_complaints.filter(status__in=['Pending Review', 'Assigned', 'Under Investigation', 'FIR Registered', 'Case Active']).count(),
        'resolved_complaints': user_complaints.filter(status='Resolved').count(),
        'sos_count': user_sos.count(),
        'recent_complaints': [_complaint_to_dict(c) for c in user_complaints[:4]],
    })


def complaint_form(request):
    user = get_current_user(request)
    stations = PoliceStation.objects.all()
    locations = Location.objects.all().order_by('name')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category = request.POST.get('category', '').strip().title()
        description = request.POST.get('description', '').strip()
        incident_date = request.POST.get('incident_date', '') or datetime.now().strftime('%Y-%m-%d')
        incident_time = request.POST.get('incident_time', '') or datetime.now().strftime('%H:%M')
        address = request.POST.get('address', '').strip()
        area = request.POST.get('area', '').strip()
        street = request.POST.get('street', '').strip()
        city = request.POST.get('city', '').strip() or 'Madurai'
        district = request.POST.get('district', '').strip() or city
        pincode = request.POST.get('pincode', '').strip() or '625001'
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()
        evidence = request.POST.get('evidence', '') or 'complaint_doc.pdf'

        # Look up location coordinates from Area if not provided
        if area and (not latitude or not longitude):
            loc_obj = Location.objects.filter(name__iexact=area).first()
            if loc_obj:
                latitude = loc_obj.latitude
                longitude = loc_obj.longitude

        # Fallback to user registered coordinates if not specified
        if (not latitude or not longitude) and user.get('latitude'):
            latitude = user.get('latitude')
            longitude = user.get('longitude')

        # 1. Geographic / Jurisdiction Routing to nearest Police Station
        matched_station, dist_km, match_reason = find_jurisdiction_station(
            complaint_lat=latitude, complaint_lon=longitude,
            city=city, pincode=pincode, address=f"{area} {address}",
            stations=list(stations)
        )

        station_id = matched_station.station_id if matched_station else 'PS-001'
        station_name = matched_station.name if matched_station else 'Primary Police Station'

        # 2. AI Duplicate Detection Engine
        existing_complaints = Complaint.objects.all()
        dup_result = check_duplicate_complaint(
            new_title=title, new_desc=description, new_category=category,
            existing_complaints=list(existing_complaints)
        )

        count = Complaint.objects.count()
        new_complaint = Complaint.objects.create(
            complaint_id=f"CMP-{count + 1:03d}",
            citizen_name=user.get('name', 'Citizen'),
            citizen_email=user.get('email', ''),
            citizen_phone=user.get('phone', ''),
            title=title,
            category=category,
            description=description,
            incident_date=incident_date,
            incident_time=incident_time,
            address=address,
            area=area,
            street=street,
            city=city,
            district=district,
            pincode=pincode,
            latitude=latitude or (matched_station.latitude if matched_station else '9.9252'),
            longitude=longitude or (matched_station.longitude if matched_station else '78.1198'),
            evidence=evidence,
            assigned_station_id=station_id,
            assigned_station_name=station_name,
            status='Pending Review',
            fir_status='Not Filed',
            case_status='Not Assigned',
            ai_duplicate_flag='Possible Duplicate' if dup_result['is_duplicate'] else 'Unique',
            ai_similarity_score=f"{dup_result['similarity_pct']}%",
            ai_matched_complaint_id=dup_result['matched_complaint_id'] or '',
            ai_matched_title=dup_result['matched_title'] or '',
            created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        return redirect(f'/citizen/complaint/detail/?id={new_complaint.complaint_id}')

    return render(request, 'firstapp/complaint_form.html', {
        'current_user': user,
        'stations': stations,
        'locations': locations,
    })


def complaints(request):
    user = get_current_user(request)
    if user.get('role') == 'citizen':
        qs = Complaint.objects.filter(
            Q(citizen_email__iexact=user.get('email', '')) | Q(citizen_email__iexact=user.get('personal_email', ''))
        )
    else:
        qs = Complaint.objects.all()
    return render(request, 'firstapp/complaints.html', {
        'current_user': user,
        'complaints': [_complaint_to_dict(c) for c in qs]
    })


def complaint_detail(request):
    user = get_current_user(request)
    complaint_id = request.GET.get('id', '')
    if user.get('role') == 'citizen':
        qs = Complaint.objects.filter(
            Q(citizen_email__iexact=user.get('email', '')) | Q(citizen_email__iexact=user.get('personal_email', ''))
        )
    else:
        qs = Complaint.objects.all()

    obj = qs.filter(complaint_id=complaint_id).first() or qs.first()
    return render(request, 'firstapp/complaint_detail.html', {
        'current_user': user,
        'complaint': _complaint_to_dict(obj) if obj else None
    })


def sos(request):
    user = get_current_user(request)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if request.method == 'POST':
        count = SOS.objects.count()
        new_id = f"SOS-{count + 1:03d}"
        SOS.objects.create(
            sos_id=new_id,
            citizen_name=user.get('name', ''),
            citizen_email=user.get('email', ''),
            citizen_phone=user.get('phone', ''),
            time=now_str,
            location=request.POST.get('location', 'Emergency Location, Madurai'),
            latitude=request.POST.get('latitude', '9.9135'),
            longitude=request.POST.get('longitude', '78.1205'),
            status='Active'
        )
        return JsonResponse({'status': 'success', 'sos_id': new_id})
    return render(request, 'firstapp/sos.html', {'current_user': user, 'current_time': now_str})


def missing_person(request):
    user = get_current_user(request)
    today_str = datetime.now().strftime('%Y-%m-%d')
    if request.method == 'POST':
        count = MissingPerson.objects.count()
        MissingPerson.objects.create(
            person_id=f"MIS-{count + 1:03d}",
            name=request.POST.get('person_name', '').strip(),
            age=request.POST.get('age', '').strip(),
            gender=request.POST.get('gender', '').strip().title(),
            last_seen_date=request.POST.get('last_seen_date', '') or today_str,
            last_seen_location=request.POST.get('last_seen_location', '').strip(),
            description=request.POST.get('description', '').strip(),
            reported_by=user.get('name', ''),
            reported_date=today_str,
            status='Missing'
        )
        return redirect('missing_person')
    return render(request, 'firstapp/missing_person.html', {
        'current_user': user,
        'missing_persons': list(MissingPerson.objects.values())
    })


def lost_found(request):
    user = get_current_user(request)
    today_str = datetime.now().strftime('%Y-%m-%d')
    if request.method == 'POST':
        report_type = request.POST.get('report_type', 'lost').strip().lower()
        item_type = request.POST.get('item_type', 'other').strip()
        count = LostFound.objects.count()
        LostFound.objects.create(
            item_id=f"LF-{count + 1:03d}",
            item_type=item_type,
            name=request.POST.get('item_name', '').strip(),
            category=item_type.title(),
            description=request.POST.get('description', '').strip(),
            location=request.POST.get('location', '').strip(),
            date=request.POST.get('date', '') or today_str,
            reported_by=user.get('name', ''),
            report_type=report_type,
            status='Lost' if report_type == 'lost' else 'Found'
        )
        return redirect('lost_found')
    return render(request, 'firstapp/lost_found.html', {
        'current_user': user,
        'items': list(LostFound.objects.values())
    })


def community_alerts(request):
    user = get_current_user(request)
    return render(request, 'firstapp/community_alerts.html', {
        'current_user': user,
        'alerts': list(Alert.objects.values())
    })


# ==============================================================================
# 3. INSPECTOR (STATION IN-CHARGE) VIEWS & WORKFLOW
# ==============================================================================

def inspector_dashboard(request):
    user = get_current_user(request)
    station_id = user.get('station_id', '')

    # Filter station complaints
    if station_id:
        complaints_qs = Complaint.objects.filter(Q(assigned_station_id=station_id) | Q(assigned_station_name__icontains=user.get('station_name', '')))
        officers_qs = User.objects.filter(role='officer', station_id=station_id, is_verified=True)
        firs_qs = FIR.objects.filter(station_id=station_id)
        cases_qs = Case.objects.filter(station_id=station_id)
    else:
        complaints_qs = Complaint.objects.all()
        officers_qs = User.objects.filter(role='officer', is_verified=True)
        firs_qs = FIR.objects.all()
        cases_qs = Case.objects.all()

    # Handle quick Inspector actions (Assign Officer or Mark Duplicate)
    if request.method == 'POST':
        action = request.POST.get('action')
        complaint_id = request.POST.get('complaint_id')
        if action == 'assign_officer':
            officer_id = request.POST.get('officer_id')
            officer = User.objects.filter(id=officer_id).first() or User.objects.filter(email=officer_id).first() or User.objects.filter(official_email=officer_id).first()
            if officer:
                Complaint.objects.filter(complaint_id=complaint_id).update(
                    assigned_officer_id=officer.official_email or officer.email,
                    assigned_officer_name=officer.name,
                    assigned_by_inspector=user.get('name', 'Inspector'),
                    assigned_date=datetime.now().strftime('%Y-%m-%d %H:%M'),
                    status='Assigned'
                )
        elif action == 'mark_duplicate':
            reason = request.POST.get('reason', 'Identified as duplicate of another complaint')
            Complaint.objects.filter(complaint_id=complaint_id).update(
                status='Duplicate / Ignored',
                rejection_reason=reason
            )
        return redirect('inspector_dashboard')

    return render(request, 'firstapp/inspector_dashboard.html', {
        'current_user': user,
        'station_name': user.get('station_name') or user.get('station') or 'All Stations',
        'pending_review_count': complaints_qs.filter(status__in=['Pending Review', 'Pending']).count(),
        'duplicate_flagged_count': complaints_qs.filter(ai_duplicate_flag='Possible Duplicate').count(),
        'assigned_count': complaints_qs.filter(status__in=['Assigned', 'Under Investigation']).count(),
        'active_firs_count': firs_qs.count(),
        'active_cases_count': cases_qs.exclude(status='Closed').count(),
        'station_complaints': [_complaint_to_dict(c) for c in complaints_qs[:10]],
        'station_officers': list(officers_qs.values()),
        'monitored_cases': list(cases_qs[:8]),
    })


def inspector_monitoring(request):
    user = get_current_user(request)
    station_id = user.get('station_id', '')

    if station_id:
        officers = User.objects.filter(role='officer', station_id=station_id, is_verified=True)
        assigned_complaints = Complaint.objects.filter(assigned_station_id=station_id).exclude(status__in=['Pending Review', 'Duplicate / Ignored'])
        cases = Case.objects.filter(station_id=station_id)
    else:
        officers = User.objects.filter(role='officer', is_verified=True)
        assigned_complaints = Complaint.objects.exclude(status__in=['Pending Review', 'Duplicate / Ignored'])
        cases = Case.objects.all()

    return render(request, 'firstapp/inspector_monitoring.html', {
        'current_user': user,
        'station_name': user.get('station_name') or user.get('station') or 'Station Jurisdiction',
        'officers': list(officers.values()),
        'assigned_complaints': [_complaint_to_dict(c) for c in assigned_complaints],
        'cases': list(cases.values()),
    })


# ==============================================================================
# 4. POLICE OFFICER (INVESTIGATING OFFICER) VIEWS & WORKFLOW
# ==============================================================================

def officer_dashboard(request):
    user = get_current_user(request)
    officer_email = user.get('email', '')
    officer_official = user.get('official_email', '')
    officer_name = user.get('name', '')

    # Officer sees complaints assigned directly to them
    my_complaints = Complaint.objects.filter(
        Q(assigned_officer_id__iexact=officer_email) |
        Q(assigned_officer_id__iexact=officer_official) |
        Q(assigned_officer_name__iexact=officer_name)
    )
    my_cases = Case.objects.filter(
        Q(assigned_officer__icontains=officer_name) | Q(officer_badge=user.get('badge_number', ''))
    )

    # Actions: Close/Reject or Add Investigation Notes
    if request.method == 'POST':
        action = request.POST.get('action')
        complaint_id = request.POST.get('complaint_id')
        if action == 'add_notes':
            notes = request.POST.get('investigation_notes', '').strip()
            Complaint.objects.filter(complaint_id=complaint_id).update(
                investigation_notes=notes,
                status='Under Investigation'
            )
        elif action == 'close_invalid':
            reason = request.POST.get('rejection_reason', 'Found invalid during preliminary inquiry').strip()
            Complaint.objects.filter(complaint_id=complaint_id).update(
                status='Closed / Rejected',
                rejection_reason=reason
            )
        return redirect('officer_dashboard')

    return render(request, 'firstapp/officer_dashboard.html', {
        'current_user': user,
        'assigned_complaints': [_complaint_to_dict(c) for c in my_complaints],
        'active_investigations_count': my_complaints.filter(status='Under Investigation').count(),
        'assigned_count': my_complaints.filter(status='Assigned').count(),
        'firs_registered_count': my_complaints.filter(status='FIR Registered').count(),
        'my_cases': list(my_cases.values()),
        'total_cases_count': my_cases.count(),
    })


def police_dashboard(request):
    """Smart router to redirect to inspector or officer dashboard based on user role."""
    user = get_current_user(request)
    if user.get('role') == 'inspector':
        return redirect('inspector_dashboard')
    elif user.get('role') in ['officer', 'police']:
        return redirect('officer_dashboard')
    elif user.get('role') == 'admin':
        return redirect('admin_dashboard')
    return redirect('citizen_dashboard')


def police_complaints(request):
    user = get_current_user(request)
    role = user.get('role', 'officer')

    if role == 'inspector':
        return redirect('inspector_dashboard')

    # For Officer: View my assigned complaints
    officer_email = user.get('email', '')
    officer_official = user.get('official_email', '')
    officer_name = user.get('name', '')
    all_complaints = Complaint.objects.filter(
        Q(assigned_officer_id__iexact=officer_email) |
        Q(assigned_officer_id__iexact=officer_official) |
        Q(assigned_officer_name__iexact=officer_name)
    )

    selected_id = request.GET.get('view_id', '')
    selected = all_complaints.filter(complaint_id=selected_id).first() or all_complaints.first()

    return render(request, 'firstapp/police_complaints.html', {
        'current_user': user,
        'complaints': [_complaint_to_dict(c) for c in all_complaints],
        'selected_complaint': _complaint_to_dict(selected) if selected else None,
    })


def fir(request):
    user = get_current_user(request)
    today_str = datetime.now().strftime('%Y-%m-%d')

    if request.method == 'POST':
        complaint_id = request.POST.get('complaint_id', '').strip()
        section_of_law = request.POST.get('section_of_law', '').strip()
        description = request.POST.get('description', '').strip()
        status = request.POST.get('status', 'FIR Registered').strip()

        count = FIR.objects.count()
        fir_id = f"FIR-{count + 1:03d}"
        FIR.objects.create(
            fir_id=fir_id,
            complaint_id=complaint_id,
            station_id=user.get('station_id', ''),
            station_name=user.get('station_name', '') or user.get('station', ''),
            investigating_officer=user.get('name', ''),
            officer_badge=user.get('badge_number', ''),
            section_of_law=section_of_law,
            fir_date=request.POST.get('fir_date', '') or today_str,
            description=description,
            status=status
        )

        # Update Complaint Status
        Complaint.objects.filter(complaint_id=complaint_id).update(
            status='FIR Registered',
            fir_status='FIR Registered',
            case_status='Case Active'
        )

        # Auto-create Case record for investigation
        case_count = Case.objects.count()
        Case.objects.create(
            case_id=f"CASE-{case_count + 1:03d}",
            fir_id=fir_id,
            complaint_id=complaint_id,
            station_id=user.get('station_id', ''),
            assigned_officer=user.get('name', ''),
            officer_badge=user.get('badge_number', ''),
            status='Investigation in Progress',
            start_date=today_str,
            description=f"FIR filed under {section_of_law}. Investigation initiated by {user.get('name', 'Officer')}.",
            last_update=today_str
        )

        return redirect('cases')

    all_firs = FIR.objects.all()
    if user.get('station_id'):
        all_firs = all_firs.filter(station_id=user.get('station_id'))

    return render(request, 'firstapp/fir.html', {
        'current_user': user,
        'firs': list(all_firs.values()),
        'next_fir_id': f"FIR-{FIR.objects.count() + 1:03d}",
    })


def cases(request):
    user = get_current_user(request)
    all_cases = Case.objects.all()
    if user.get('role') == 'officer':
        all_cases = all_cases.filter(
            Q(assigned_officer__icontains=user.get('name', '')) | Q(officer_badge=user.get('badge_number', ''))
        )

    # Handle Case Update
    if request.method == 'POST':
        case_id = request.POST.get('case_id')
        new_status = request.POST.get('status')
        accused_info = request.POST.get('accused_info', '')
        witnesses = request.POST.get('witnesses', '')
        summary = request.POST.get('investigation_summary', '')

        Case.objects.filter(case_id=case_id).update(
            status=new_status,
            accused_info=accused_info,
            witnesses=witnesses,
            investigation_summary=summary,
            last_update=datetime.now().strftime('%Y-%m-%d %H:%M')
        )
        return redirect(f'/police/cases/?id={case_id}')

    selected_id = request.GET.get('id', '')
    selected = all_cases.filter(case_id=selected_id).first() or all_cases.first()

    return render(request, 'firstapp/cases.html', {
        'current_user': user,
        'cases': list(all_cases.values()),
        'selected_case': {f.name: getattr(selected, f.name) for f in selected._meta.fields} if selected else None,
    })


def evidence(request):
    user = get_current_user(request)
    if request.method == 'POST':
        count = Evidence.objects.count()
        Evidence.objects.create(
            evidence_id=f"EVD-{count + 1:03d}",
            complaint_id=request.POST.get('complaint_id', 'CMP-001'),
            file_name=request.POST.get('file_name', 'evidence_doc.pdf'),
            file_type=request.POST.get('file_type', 'Document'),
            file_size=request.POST.get('file_size', '2.4 MB'),
            uploaded_date=datetime.now().strftime('%Y-%m-%d'),
            added_by=user.get('name', 'Officer')
        )
        return redirect('evidence')

    return render(request, 'firstapp/evidence.html', {
        'current_user': user,
        'evidence_records': list(Evidence.objects.values())
    })


def accused(request):
    user = get_current_user(request)
    if request.method == 'POST':
        count = Accused.objects.count()
        Accused.objects.create(
            accused_id=f"ACC-{count + 1:03d}",
            name=request.POST.get('name', '').strip(),
            gender=request.POST.get('gender', 'Male'),
            phone=request.POST.get('phone', ''),
            address=request.POST.get('address', ''),
            criminal_status=request.POST.get('criminal_status', 'Suspect'),
            marks=request.POST.get('marks', ''),
            associated_cases=request.POST.get('associated_cases', '')
        )
        return redirect('accused')

    all_accused = Accused.objects.all()
    selected_id = request.GET.get('id', '')
    selected = all_accused.filter(accused_id=selected_id).first() or all_accused.first()

    return render(request, 'firstapp/accused.html', {
        'current_user': user,
        'accused_records': list(all_accused.values()),
        'selected_accused': {f.name: getattr(selected, f.name) for f in selected._meta.fields} if selected else None,
    })


def police_sos(request):
    user = get_current_user(request)
    action = request.GET.get('action')
    sos_id = request.GET.get('id')
    if action == 'resolve' and sos_id:
        SOS.objects.filter(sos_id=sos_id).update(status='Resolved')
        return redirect('police_sos')
    return render(request, 'firstapp/police_sos.html', {
        'current_user': user,
        'sos_alerts': list(SOS.objects.values())
    })


def crime_intelligence(request):
    user = get_current_user(request)
    complaints_qs = Complaint.objects.all()
    return render(request, 'firstapp/crime_intelligence.html', {
        'current_user': user,
        'total_complaints': complaints_qs.count(),
        'theft_count': complaints_qs.filter(category__icontains='theft').count(),
        'cyber_count': complaints_qs.filter(category__icontains='cyber').count(),
        'accident_count': complaints_qs.filter(category__icontains='accident').count(),
        'harassment_count': complaints_qs.filter(category__icontains='harass').count(),
        'fraud_count': complaints_qs.filter(category__icontains='fraud').count(),
    })


# ==============================================================================
# 5. ADMIN VIEWS (STATIONS & OFFICERS VERIFICATION / ASSIGNMENT ONLY)
# ==============================================================================

def admin_dashboard(request):
    user = get_current_user(request)
    users_qs = User.objects.all()
    stations_qs = PoliceStation.objects.all()

    return render(request, 'firstapp/admin_dashboard.html', {
        'current_user': user,
        'citizens_count': users_qs.filter(role='citizen').count(),
        'inspectors_count': users_qs.filter(role='inspector', is_verified=True).count(),
        'officers_count': users_qs.filter(role__in=['officer', 'police'], is_verified=True).count(),
        'pending_police_count': users_qs.filter(role='police', is_verified=False).count(),
        'stations_count': stations_qs.count(),
        'total_complaints': Complaint.objects.count(),
        'total_cases': Case.objects.count(),
        'recent_users': list(users_qs.order_by('-id').values()[:5]),
        'recent_stations': list(stations_qs.values()[:4]),
    })


def users(request):
    user = get_current_user(request)
    stations = PoliceStation.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')

        # Admin Verifies & Assigns Posting to a Registered Police Applicant
        if action == 'verify_police':
            user_id = request.POST.get('user_id')
            official_email = request.POST.get('official_email', '').strip().lower()
            role = request.POST.get('role', 'officer').strip()
            station_id = request.POST.get('station_id', '').strip()
            rank = request.POST.get('rank', '').strip()
            badge_number = request.POST.get('badge_number', '').strip()

            st_obj = PoliceStation.objects.filter(station_id=station_id).first()
            station_name = st_obj.name if st_obj else ''

            police_user = User.objects.filter(id=user_id).first()
            if police_user:
                # Ensure @tnpolice.gov.in domain
                if not official_email.endswith('@tnpolice.gov.in'):
                    clean_name = police_user.name.lower().replace(' ', '.')
                    official_email = f"{clean_name}@tnpolice.gov.in"

                police_user.official_email = official_email
                police_user.email = official_email  # Set as primary login email
                police_user.role = role
                police_user.station_id = station_id
                police_user.station_name = station_name
                police_user.station = station_name
                police_user.rank = rank or ('Inspector (Station In-Charge)' if role == 'inspector' else 'Sub Inspector')
                police_user.badge_number = badge_number
                police_user.is_verified = True
                police_user.approval_status = 'approved'
                police_user.save()

                # If assigned as Inspector, designate as Station In-Charge
                if role == 'inspector' and st_obj:
                    st_obj.incharge_inspector_id = official_email
                    st_obj.incharge_inspector_name = police_user.name
                    st_obj.save()

            return redirect('users')

        # Direct Admin Personnel Addition
        elif action == 'add_personnel':
            full_name = request.POST.get('full_name', '').strip()
            official_email = request.POST.get('email', '').strip().lower()
            badge_number = request.POST.get('badge_number', '').strip()
            role = request.POST.get('role', 'officer')
            station_id = request.POST.get('station_id')
            rank = request.POST.get('rank', '')

            if not official_email.endswith('@tnpolice.gov.in'):
                clean_name = full_name.lower().replace(' ', '.')
                official_email = f"{clean_name}@tnpolice.gov.in"

            st_obj = PoliceStation.objects.filter(station_id=station_id).first()
            station_name = st_obj.name if st_obj else ''

            new_officer, _ = User.objects.update_or_create(
                email=official_email,
                defaults={
                    'name': full_name,
                    'official_email': official_email,
                    'personal_email': official_email,
                    'badge_number': badge_number,
                    'role': role,
                    'station_id': station_id,
                    'station_name': station_name,
                    'station': station_name,
                    'rank': rank or ('Inspector (Station In-Charge)' if role == 'inspector' else 'Sub Inspector'),
                    'password': 'password123',
                    'is_verified': True,
                    'approval_status': 'approved',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            )

            if role == 'inspector' and st_obj:
                st_obj.incharge_inspector_id = official_email
                st_obj.incharge_inspector_name = full_name
                st_obj.save()

            return redirect('users')

    all_users = User.objects.all()
    return render(request, 'firstapp/users.html', {
        'current_user': user,
        'pending_police': list(all_users.filter(role='police', is_verified=False).values()),
        'inspectors': list(all_users.filter(role='inspector', is_verified=True).values()),
        'police_officers': list(all_users.filter(role='officer', is_verified=True).values()),
        'citizens': list(all_users.filter(role='citizen').values()),
        'stations': list(stations.values()),
    })


def police_stations(request):
    user = get_current_user(request)
    all_stations = PoliceStation.objects.all()
    inspectors = User.objects.filter(role='inspector', is_verified=True)

    if request.method == 'POST':
        station_name = request.POST.get('station_name', '').strip()
        district = request.POST.get('district', 'Madurai').strip()
        address = request.POST.get('address', '').strip()
        latitude = request.POST.get('latitude', '').strip() or '9.9252'
        longitude = request.POST.get('longitude', '').strip() or '78.1198'
        contact = request.POST.get('contact', '').strip()
        incharge_email = request.POST.get('incharge_inspector_id', '')

        incharge_name = ''
        if incharge_email:
            insp = User.objects.filter(Q(email=incharge_email) | Q(official_email=incharge_email)).first()
            if insp:
                incharge_name = insp.name

        count = all_stations.count()
        new_station = PoliceStation.objects.create(
            station_id=f"PS-{count + 1:03d}",
            name=station_name,
            district=district,
            address=address,
            latitude=latitude,
            longitude=longitude,
            contact=contact,
            incharge_inspector_id=incharge_email,
            incharge_inspector_name=incharge_name
        )

        if incharge_email:
            User.objects.filter(Q(email=incharge_email) | Q(official_email=incharge_email)).update(
                station_id=new_station.station_id,
                station_name=new_station.name,
                station=new_station.name
            )

        return redirect('police_stations')

    return render(request, 'firstapp/police_stations.html', {
        'current_user': user,
        'stations': list(all_stations.values()),
        'inspectors': list(inspectors.values()),
        'next_station_id': f"PS-{all_stations.count() + 1:03d}",
    })


def admin_alerts(request):
    user = get_current_user(request)
    today_str = datetime.now().strftime('%Y-%m-%d')
    action = request.GET.get('action')
    alert_id = request.GET.get('id')
    if action == 'delete' and alert_id:
        Alert.objects.filter(alert_id=alert_id).delete()
        return redirect('admin_alerts')

    if request.method == 'POST':
        count = Alert.objects.count()
        Alert.objects.create(
            alert_id=f"ALT-{count + 1:03d}",
            title=request.POST.get('title', '').strip(),
            description=request.POST.get('description', '').strip(),
            area=request.POST.get('area', '').strip(),
            created_date=request.POST.get('created_date', '') or today_str,
            expiry_date=request.POST.get('expiry_date', '') or 'Active 48h',
            status='Active',
            badge_class='badge-warning'
        )
        return redirect('admin_alerts')

    return render(request, 'firstapp/admin_alerts.html', {
        'current_user': user,
        'alerts': list(Alert.objects.values())
    })


# ==============================================================================
# 6. FEEDBACK
# ==============================================================================

def feedback(request):
    user = get_current_user(request)
    if request.method == 'POST':
        count = Feedback.objects.count()
        Feedback.objects.create(
            feedback_id=f"FB-{count + 1:03d}",
            full_name=request.POST.get('full_name', '').strip(),
            email=request.POST.get('email', '').strip(),
            phone=request.POST.get('phone', '').strip(),
            rating=str(request.POST.get('rating', '5')),
            products_used=", ".join(request.POST.getlist('products_used')),
            feedback=request.POST.get('feedback', '').strip(),
            submitted_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        return redirect('thankyou')
    return render(request, 'firstapp/feedback.html', {'current_user': user})


def thankyou(request):
    return render(request, 'firstapp/thankyou.html')
