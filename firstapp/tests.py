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


class SOSRoutingTests(TestCase):
    def setUp(self):
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
