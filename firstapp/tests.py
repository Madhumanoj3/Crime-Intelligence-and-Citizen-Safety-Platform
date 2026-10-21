# pyrefly: ignore [missing-import]
from unittest import mock

from django.test import TestCase

from . import priority_predictor
from .models import SOS, Complaint, Location, PoliceStation, User

HIGH_TEXT = ('A man was stabbed with a knife near the bus stand and is bleeding heavily. '
             'The attackers with weapons are still around and threatened to kill us.')
LOW_TEXT = 'Someone drew graffiti on our compound wall. It is a minor issue and nobody was hurt.'


class PriorityFlowTests(TestCase):
    """Citizen submits -> AI predicts priority -> stored -> Inspector sees it -> normal workflow continues."""

    def setUp(self):
        PoliceStation.objects.create(station_id='PS-T01', name='Test Police Station', address='Test',
                                     latitude='9.9252', longitude='78.1198')
        Location.objects.create(name='Test Bus Stand', latitude='9.9252', longitude='78.1198',
                                location_type='Landmark')
        User.objects.create(name='Citizen One', email='citizen@test.com', password='pw', role='citizen')
        User.objects.create(name='Insp Test', email='insp@tnpolice.gov.in', password='pw', role='inspector',
                            station_id='PS-T01', station_name='Test Police Station')
        self.officer = User.objects.create(name='Officer Ravi', email='ravi@tnpolice.gov.in', password='pw',
                                           role='officer', station_id='PS-T01', badge_number='TN-1')

    def login(self, email):
        resp = self.client.post('/login/', {'email': email, 'password': 'pw'})
        self.assertEqual(resp.status_code, 302, 'login should redirect to a dashboard')

    def submit(self, title, description, category, incident_time='23:30'):
        self.login('citizen@test.com')
        resp = self.client.post('/citizen/complaint/new/', {
            'title': title, 'category': category, 'description': description,
            'incident_date': '2026-09-20', 'incident_time': incident_time,
            'area': 'Test Bus Stand', 'city': 'Madurai', 'pincode': '625001',
        })
        self.assertEqual(resp.status_code, 302)
        return Complaint.objects.order_by('-pk').first()

    def test_full_flow(self):
        # 1-4. Citizen submits; complaint saved normally with a stored AI priority.
        c = self.submit('Stabbing near bus stand', HIGH_TEXT, 'assault')
        self.assertEqual(c.category, 'Assault')
        self.assertEqual(c.ai_priority, 'High')
        self.assertTrue(c.ai_priority_confidence.endswith('%'))
        # Prediction must not change the workflow: still pending, nobody assigned.
        self.assertEqual(c.status, 'Pending Review')
        self.assertEqual(c.assigned_officer_name, '')
        self.assertEqual(c.assigned_station_id, 'PS-T01')

        # Citizen detail page does not show the AI priority.
        detail = self.client.get(f'/citizen/complaint/detail/?id={c.complaint_id}').content.decode()
        self.assertNotIn('AI Predicted Priority', detail)

        # 5. Inspector dashboard shows priority badge, explanation and duplicate check.
        self.login('insp@tnpolice.gov.in')
        page = self.client.get('/inspector/dashboard/').content.decode()
        self.assertIn(c.complaint_id, page)
        self.assertIn('AI Predicted Priority', page)
        self.assertIn('badge-priority-high', page)
        self.assertIn('provided only as decision support', page)
        self.assertIn('AI Duplicate Check', page)

        # Inspector detail page shows priority and note.
        detail = self.client.get(f'/citizen/complaint/detail/?id={c.complaint_id}').content.decode()
        self.assertIn('AI Predicted Priority', detail)
        self.assertIn('badge-priority-high', detail)
        self.assertIn('Back to Station Complaint Queue', detail)

        # 6. Inspector assigns one officer manually; priority is kept.
        self.client.post('/inspector/dashboard/', {'action': 'assign_officer', 'complaint_id': c.complaint_id,
                                                   'officer_id': self.officer.id})
        c.refresh_from_db()
        self.assertEqual(c.status, 'Assigned')
        self.assertEqual(c.assigned_officer_name, 'Officer Ravi')
        self.assertEqual(c.ai_priority, 'High')

    def test_low_priority_complaint(self):
        c = self.submit('Graffiti on wall', LOW_TEXT, 'vandalism', incident_time='11:00')
        self.assertEqual(c.ai_priority, 'Low')
        self.login('insp@tnpolice.gov.in')
        self.assertIn('badge-priority-low', self.client.get('/inspector/dashboard/').content.decode())

    def test_duplicate_detection_still_works(self):
        self.submit('Stabbing near bus stand', HIGH_TEXT, 'assault')
        second = self.submit('Stabbing near bus stand', HIGH_TEXT, 'assault')
        self.assertEqual(second.ai_duplicate_flag, 'Possible Duplicate')
        self.assertTrue(second.ai_priority)
        # Inspector can still mark it duplicate manually.
        self.login('insp@tnpolice.gov.in')
        self.client.post('/inspector/dashboard/', {'action': 'mark_duplicate', 'complaint_id': second.complaint_id})
        second.refresh_from_db()
        self.assertEqual(second.status, 'Duplicate / Ignored')

    def test_missing_model_does_not_block_submission(self):
        with mock.patch.object(priority_predictor, 'MODEL_PATH', 'does/not/exist.joblib'):
            c = self.submit('Stabbing near bus stand', HIGH_TEXT, 'assault')
        self.assertEqual(c.ai_priority, '')
        self.assertEqual(c.status, 'Pending Review')
        self.login('insp@tnpolice.gov.in')
        self.assertIn('Not predicted', self.client.get('/inspector/dashboard/').content.decode())

    def test_hotspots_api_still_works(self):
        self.submit('Stabbing near bus stand', HIGH_TEXT, 'assault')
        self.assertEqual(self.client.get('/api/hotspots/').status_code, 200)

    def test_previous_reports_counted(self):
        self.submit('Theft one', 'My mobile phone was stolen.', 'theft')
        second = self.submit('Theft two', 'My bicycle was stolen.', 'theft')
        result = priority_predictor.apply_ai_priority(second)
        self.assertEqual(result['previous_reports'], 1)
        self.assertEqual(result['location_type'], 'Landmark')

    def test_inspector_sees_all_complaints(self):
        ids = [self.submit(f'Complaint {i}', f'Unique incident number {i} happened today.', 'other').complaint_id
               for i in range(12)]
        self.login('insp@tnpolice.gov.in')
        page = self.client.get('/inspector/dashboard/').content.decode()
        for cid in ids:
            self.assertIn(f'<strong>{cid}</strong>', page)
        # Newest complaint is listed first.
        self.assertLess(page.find(f'<strong>{ids[-1]}</strong>'), page.find(f'<strong>{ids[0]}</strong>'))

    def test_assign_officer_with_long_email(self):
        long_email = 'si.assistant_commissioner_of_madurai_town@tnpolice.gov.in'  # 57 chars, like real data
        officer = User.objects.create(name='SI Long Email', email=long_email, official_email=long_email,
                                      password='pw', role='officer', station_id='PS-T01')
        c = self.submit('Stabbing near bus stand', HIGH_TEXT, 'assault')
        self.login('insp@tnpolice.gov.in')
        resp = self.client.post('/inspector/dashboard/', {'action': 'assign_officer',
                                                          'complaint_id': c.complaint_id, 'officer_id': officer.id})
        self.assertEqual(resp.status_code, 302)
        c.refresh_from_db()
        self.assertEqual(c.assigned_officer_id, long_email)
        self.assertEqual(c.status, 'Assigned')
        # The officer sees the assigned complaint on their own dashboard.
        self.client.post('/login/', {'email': long_email, 'password': 'pw'})
        self.assertIn(c.complaint_id, self.client.get('/officer/dashboard/').content.decode())


class SidebarTests(TestCase):
    """Inspector / officer keep their own sidebar on every shared police page."""
    PAGES = {'fir': '/police/fir/', 'cases': '/police/cases/', 'evidence': '/police/evidence/',
             'accused': '/police/accused/', 'police_sos': '/police/sos/',
             'crime_intelligence': '/police/crime-intelligence/'}

    def setUp(self):
        from django.urls import reverse
        self.PAGES = {name: reverse(name) for name in self.PAGES}
        User.objects.create(name='Insp', email='insp@tnpolice.gov.in', password='pw', role='inspector')
        User.objects.create(name='Off', email='off@tnpolice.gov.in', password='pw', role='officer')

    def sidebar(self, url):
        html = self.client.get(url).content.decode()
        return html[html.find('<aside class="sidebar">'):html.find('</aside>')]

    def check_role(self, email, header, own_pages):
        self.client.post('/login/', {'email': email, 'password': 'pw'})
        from django.urls import reverse
        for name, url in {**self.PAGES, **{p: reverse(p) for p in own_pages}}.items():
            side = self.sidebar(url)
            self.assertIn(header, side, f'{email} on {url}')
            self.assertNotIn('Police Panel', side, f'{email} on {url}')
            self.assertIn(f'<a href="{url}" class="active">', side, f'active link on {url}')
            self.assertEqual(side.count('class="active"'), 1, url)

    def test_inspector_sidebar(self):
        self.check_role('insp@tnpolice.gov.in', 'Inspector (Station In-Charge)',
                        ['inspector_dashboard', 'inspector_monitoring'])

    def test_officer_sidebar(self):
        self.check_role('off@tnpolice.gov.in', 'Police Officer (IO)', ['officer_dashboard'])

    def test_admin_keeps_police_panel(self):
        self.client.post('/login/', {'email': 'admin@gmail.com', 'password': 'admin123'})
        self.assertIn('Police Panel', self.sidebar(self.PAGES['fir']))


def login_as(client, role, email='user@test.com', **extra):
    """Create a verified user with this role and log the test client in as them."""
    user = User.objects.create(name=extra.pop('name', 'Test User'), email=email, password='pw', role=role,
                               is_verified=True, approval_status='approved', **extra)
    client.post('/login/', {'email': email, 'password': 'pw'})
    return user


class SOSRoutingTests(TestCase):
    def setUp(self):
        login_as(self.client, 'citizen')
        PoliceStation.objects.create(station_id='PS-A', name='Near Station', address='a',
                                     latitude='9.9252', longitude='78.1198')
        PoliceStation.objects.create(station_id='PS-B', name='Far Station', address='b',
                                     latitude='13.0827', longitude='80.2707')

    def test_sos_goes_to_nearest_station_with_description(self):
        resp = self.client.post('/citizen/sos/', {
            'description': 'Being followed', 'latitude': '9.93', 'longitude': '78.12'})
        self.assertEqual(resp.status_code, 200)
        sos = SOS.objects.get()
        self.assertEqual(sos.assigned_station_id, 'PS-A')
        self.assertEqual(sos.description, 'Being followed')

    def test_sos_requires_description(self):
        resp = self.client.post('/citizen/sos/', {'latitude': '9.93', 'longitude': '78.12'})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(SOS.objects.count(), 0)


class LandmarkComplaintTests(TestCase):
    def setUp(self):
        from .models import Landmark
        login_as(self.client, 'citizen')
        PoliceStation.objects.create(station_id='PS-A', name='Near Station', address='a',
                                     latitude='9.9100', longitude='78.1200')
        PoliceStation.objects.create(station_id='PS-B', name='Far Station', address='b',
                                     latitude='9.9500', longitude='78.1000')
        Location.objects.create(name='Sellur', latitude='9.95000', longitude='78.10000', location_type='Suburb')
        Landmark.objects.create(landmark_id='LM-1', name='Test Temple', landmark_type='Temple',
                                latitude='9.91000', longitude='78.12000', area='Sellur')

    def test_landmark_coordinates_override_area_and_route_station(self):
        resp = self.client.post('/citizen/complaint/new/', {
            'title': 'Chain snatching', 'category': 'theft', 'description': 'Chain stolen near the temple',
            'area': 'Sellur', 'landmark': 'test temple', 'latitude': '9.95000', 'longitude': '78.10000'})
        self.assertEqual(resp.status_code, 302)
        c = Complaint.objects.get()
        self.assertEqual(c.landmark, 'Test Temple')
        self.assertEqual(c.latitude, '9.91000')
        self.assertEqual(c.assigned_station_id, 'PS-A')

    def test_form_lists_landmarks_and_live_area_count(self):
        resp = self.client.get('/citizen/complaint/new/')
        self.assertContains(resp, 'Test Temple')
        self.assertContains(resp, 'Choose from 1 Madurai areas')


class CaseClosureTests(TestCase):
    def setUp(self):
        from .models import Case
        self.officer_client = type(self.client)()
        login_as(self.officer_client, 'officer', email='o@tnpolice.gov.in', name='O', badge_number='B')
        Complaint.objects.create(
            complaint_id='CMP-X', citizen_name='A', citizen_email='a@x.com', title='t', category='theft',
            description='d', incident_date='2026-10-01', incident_time='10:00', status='FIR Registered',
            fir_status='FIR Registered', case_status='Case Active')
        Case.objects.create(case_id='CASE-X', fir_id='FIR-X', complaint_id='CMP-X', assigned_officer='O',
                            officer_badge='B', status='Investigation in Progress', start_date='2026-10-01')

    def test_closing_case_resolves_complaint_and_citizen_dashboard(self):
        from .models import Case
        self.officer_client.post('/police/cases/', {'case_id': 'CASE-X', 'status': 'Closed'})
        c = Complaint.objects.get(complaint_id='CMP-X')
        self.assertEqual((c.status, c.case_status), ('Resolved', 'Closed'))
        self.assertNotEqual(Case.objects.get(case_id='CASE-X').end_date, '')
        login_as(self.client, 'citizen', email='a@x.com', name='A')
        resp = self.client.get('/citizen/dashboard/')
        self.assertEqual(resp.context['resolved_complaints'], 1)
        self.assertEqual(resp.context['active_complaints'], 0)

    def test_reopening_case_makes_complaint_active_again(self):
        self.officer_client.post('/police/cases/', {'case_id': 'CASE-X', 'status': 'Closed'})
        self.officer_client.post('/police/cases/', {'case_id': 'CASE-X', 'status': 'Court Trial / Hearing'})
        c = Complaint.objects.get(complaint_id='CMP-X')
        self.assertEqual((c.status, c.case_status), ('FIR Registered', 'Case Active'))


class AccessControlTests(TestCase):
    CITIZEN_PAGES = ['/citizen/dashboard/', '/citizen/complaint/new/', '/citizen/missing-person/',
                     '/citizen/lost-found/', '/citizen/community-alerts/']
    OFFICER_PAGES = ['/officer/dashboard/']
    INSPECTOR_PAGES = ['/inspector/dashboard/', '/inspector/monitoring/']
    POLICE_PAGES = ['/police/complaints/', '/police/fir/', '/police/cases/', '/police/evidence/',
                    '/police/accused/', '/police/sos/', '/police/crime-intelligence/']
    ADMIN_PAGES = ['/admin-panel/dashboard/', '/admin-panel/users/', '/admin-panel/police-stations/',
                   '/admin-panel/alerts/']
    COMMON_PAGES = ['/citizen/complaints/', '/citizen/complaint/detail/', '/police/dashboard/']

    def assert_redirects_to(self, url, target, method='get'):
        resp = getattr(self.client, method)(url)
        self.assertEqual(resp.status_code, 302, url)
        self.assertEqual(resp['Location'], target, url)

    def test_visitor_is_sent_to_login_for_every_protected_page(self):
        pages = (self.CITIZEN_PAGES + self.OFFICER_PAGES + self.INSPECTOR_PAGES + self.POLICE_PAGES
                 + self.ADMIN_PAGES + self.COMMON_PAGES)
        for url in pages:
            self.assert_redirects_to(url, '/login/')
        for url in self.OFFICER_PAGES + self.INSPECTOR_PAGES + self.POLICE_PAGES + self.ADMIN_PAGES:
            self.assert_redirects_to(url, '/login/', method='post')

    def test_visitor_gets_json_401_from_ajax_endpoints(self):
        self.assertEqual(self.client.post('/citizen/sos/', {'description': 'help'}).status_code, 401)
        self.assertEqual(self.client.get('/api/hotspots/').status_code, 401)
        self.assertEqual(SOS.objects.count(), 0)

    def test_visitor_cannot_close_a_case(self):
        from .models import Case
        Case.objects.create(case_id='CASE-V', fir_id='F', complaint_id='CMP-V', assigned_officer='O',
                            officer_badge='B', status='Investigation in Progress', start_date='2026-10-01')
        self.client.post('/police/cases/', {'case_id': 'CASE-V', 'status': 'Closed'})
        self.assertEqual(Case.objects.get().status, 'Investigation in Progress')

    def test_citizen_cannot_open_police_or_admin_pages(self):
        login_as(self.client, 'citizen')
        for url in self.OFFICER_PAGES + self.INSPECTOR_PAGES + self.POLICE_PAGES + self.ADMIN_PAGES:
            self.assert_redirects_to(url, '/citizen/dashboard/')

    def test_officer_cannot_open_citizen_inspector_or_admin_pages(self):
        login_as(self.client, 'officer', email='o@tnpolice.gov.in')
        for url in self.CITIZEN_PAGES + self.INSPECTOR_PAGES + self.ADMIN_PAGES:
            self.assert_redirects_to(url, '/officer/dashboard/')
        for url in self.POLICE_PAGES + self.OFFICER_PAGES:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_inspector_cannot_open_admin_or_officer_pages(self):
        login_as(self.client, 'inspector', email='i@tnpolice.gov.in')
        for url in self.ADMIN_PAGES + self.OFFICER_PAGES + self.CITIZEN_PAGES:
            self.assert_redirects_to(url, '/inspector/dashboard/')
        for url in self.INSPECTOR_PAGES:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_police_user_gets_json_403_on_citizen_sos(self):
        login_as(self.client, 'officer', email='o@tnpolice.gov.in')
        self.assertEqual(self.client.post('/citizen/sos/', {'description': 'x'}).status_code, 403)

    def test_admin_reaches_admin_and_police_tool_pages(self):
        self.client.post('/login/', {'email': 'admin@gmail.com', 'password': 'admin123'})
        for url in self.ADMIN_PAGES + ['/police/fir/', '/police/cases/', '/police/crime-intelligence/']:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assert_redirects_to('/citizen/dashboard/', '/admin-panel/dashboard/')

    def test_logout_removes_access(self):
        login_as(self.client, 'citizen')
        self.assertEqual(self.client.get('/citizen/dashboard/').status_code, 200)
        self.client.get('/logout/')
        self.assert_redirects_to('/citizen/dashboard/', '/login/')

    def test_public_pages_stay_public(self):
        for url in ['/', '/home/', '/login/', '/register/citizen/', '/register/police/', '/feedback/', '/thankyou/']:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_officer_cannot_update_another_officers_case(self):
        from .models import Case
        Case.objects.create(case_id='CASE-Z', fir_id='F', complaint_id='CMP-Z', assigned_officer='Someone Else',
                            officer_badge='OTHER', status='Investigation in Progress', start_date='2026-10-01')
        login_as(self.client, 'officer', email='o@tnpolice.gov.in', name='Mine', badge_number='MINE')
        self.client.post('/police/cases/', {'case_id': 'CASE-Z', 'status': 'Closed'})
        self.assertEqual(Case.objects.get().status, 'Investigation in Progress')
