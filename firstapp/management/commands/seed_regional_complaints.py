"""
Django management command to seed realistic regional complaints across Kalavasal, Mattuthavani,
Villapuram, and Nelpettai for users david@gmail.com, kabes@gmail.com, and madhu@gmail.com.

Crime Levels:
- Kalavasal: High level of crimes (predominantly High & Medium priority crimes)
- Mattuthavani: High level of crimes (predominantly High & Medium priority crimes)
- Villapuram: Medium level of crimes (predominantly Medium priority with some High/Low)
- Nelpettai: Low level of crimes (predominantly Low priority with minor complaints)
"""

from datetime import datetime, timedelta
import random
from django.core.management.base import BaseCommand
from django.db import transaction

from firstapp.models import Complaint, Location, Landmark, PoliceStation, User
from firstapp.geo_router import find_jurisdiction_station
from firstapp.priority_predictor import apply_ai_priority


class Command(BaseCommand):
    help = 'Seeds realistic complaints for Kalavasal, Mattuthavani, Villapuram, and Nelpettai.'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing regional test complaints first')

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Setting up users: david@gmail.com, kabes@gmail.com, madhu@gmail.com..."))

        # 1. Ensure the 3 requested users exist
        users_info = [
            {'email': 'david@gmail.com', 'name': 'David', 'phone': '9842112345', 'area': 'Kalavasal'},
            {'email': 'kabes@gmail.com', 'name': 'Kabes', 'phone': '9842123456', 'area': 'Mattuthavani'},
            {'email': 'madhu@gmail.com', 'name': 'Madhu', 'phone': '9842134567', 'area': 'Villapuram'},
        ]

        citizens = []
        for uinfo in users_info:
            u = User.objects.filter(email=uinfo['email']).first()
            if not u:
                u = User.objects.create(
                    name=uinfo['name'],
                    email=uinfo['email'],
                    personal_email=uinfo['email'],
                    phone=uinfo['phone'],
                    area=uinfo['area'],
                    city='Madurai',
                    state='Tamil Nadu',
                    pincode='625001',
                    password='password123',
                    role='citizen',
                    is_verified=True,
                    approval_status='approved',
                    created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                self.stdout.write(self.style.SUCCESS(f"  Created user: {u.email} ({u.name})"))
            else:
                citizens.append(u)
                self.stdout.write(self.style.SUCCESS(f"  Existing user confirmed: {u.email} ({u.name})"))
            if u not in citizens:
                citizens.append(u)

        stations = list(PoliceStation.objects.all())

        # 2. Define the complaints specification
        # Kalavasal: HIGH level (10 complaints, 5 High, 3 Medium, 2 Low)
        # Mattuthavani: HIGH level (10 complaints, 5 High, 3 Medium, 2 Low)
        # Villapuram: MEDIUM level (7 complaints, 2 High, 3 Medium, 2 Low)
        # Nelpettai: LOW level (5 complaints, 1 High, 1 Medium, 3 Low)
        complaints_specs = [
            # === KALAVASAL (HIGH CRIME REGION) ===
            {
                'area': 'Kalavasal',
                'landmark': 'Shanmuga Cinemas',
                'lat': '9.93120', 'lon': '78.09571',
                'address': 'Bypass Road, near Shanmuga Cinemas, Kalavasal',
                'title': 'Armed Highway Robbery with Deadly Weapon near Shanmuga Cinemas',
                'category': 'Theft',
                'priority': 'High',
                'confidence': '96.5%',
                'status': 'FIR Registered',
                'fir_status': 'FIR Registered',
                'case_status': 'Investigation in Progress',
                'description': 'Two masked assailants armed with a machete intercepted my two-wheeler near Shanmuga Cinemas on the bypass road at midnight. They threatened my life, assaulted me causing arm injuries, and robbed cash worth Rs. 45,000 along with my gold ring.',
                'days_ago': 2, 'time': '23:45'
            },
            {
                'area': 'Kalavasal',
                'landmark': 'Hotel Germanus',
                'lat': '9.92961', 'lon': '78.09497',
                'address': 'Theni Main Road, near Hotel Germanus, Kalavasal',
                'title': 'Night Assault and Extortion with Knife near Hotel Germanus',
                'category': 'Assault',
                'priority': 'High',
                'confidence': '94.8%',
                'status': 'Under Investigation',
                'fir_status': 'FIR Registered',
                'case_status': 'Accused Interrogated / Under Arrest',
                'description': 'A gang of three drunken individuals blocked my car near Hotel Germanus, threatened with a switchblade, demanded protection money, and physically punched me when I refused.',
                'days_ago': 4, 'time': '22:15'
            },
            {
                'area': 'Kalavasal',
                'landmark': 'Devaki Cancer and Research Institute',
                'lat': '9.92828', 'lon': '78.09857',
                'address': '26 Theni Rd, near Devaki Hospital, Kalavasal',
                'title': 'Commercial Jewelry Shop Burglary & Cash Theft on Theni Main Road',
                'category': 'Theft',
                'priority': 'High',
                'confidence': '95.2%',
                'status': 'FIR Registered',
                'fir_status': 'FIR Registered',
                'case_status': 'Investigation in Progress',
                'description': 'Our retail jewelry workshop shutters were cut open using hydraulic tools between 2 AM and 4 AM. Gold ornaments weighing 65 grams and counter locker cash were looted. CCTV shows two suspects.',
                'days_ago': 6, 'time': '03:30'
            },
            {
                'area': 'Kalavasal',
                'landmark': 'Kalavasal (Kalavasal)',
                'lat': '9.93045', 'lon': '78.09609',
                'address': 'Kalavasal Junction, near Traffic Signal',
                'title': 'Severe Physical Battery and Weapon Threat near Kalavasal Junction',
                'category': 'Assault',
                'priority': 'High',
                'confidence': '92.4%',
                'status': 'Assigned',
                'fir_status': 'Pending',
                'case_status': 'Not Assigned',
                'description': 'Violent dispute over parking turned into a brutal assault where the perpetrator struck the victim on the forehead with an iron rod, resulting in bleeding and immediate hospitalization.',
                'days_ago': 8, 'time': '19:40'
            },
            {
                'area': 'Kalavasal',
                'landmark': 'The Thangam Grand',
                'lat': '9.93184', 'lon': '78.09683',
                'address': 'Opposite The Thangam Grand, By-Pass Road, Kalavasal',
                'title': 'Coordinated Violent Snatching from Pedestrian on By-Pass Road',
                'category': 'Theft',
                'priority': 'High',
                'confidence': '91.7%',
                'status': 'FIR Registered',
                'fir_status': 'FIR Registered',
                'case_status': 'Investigation in Progress',
                'description': 'Pillion rider on an unregistered Yamaha bike dragged a walking woman onto the tarmac while forcefully snatching her 4-sovereign gold chain, causing facial lacerations.',
                'days_ago': 10, 'time': '21:10'
            },
            {
                'area': 'Kalavasal',
                'landmark': 'Vasan Eye Care Hospital',
                'lat': '9.92861', 'lon': '78.09550',
                'address': 'A.V.A.R. Plaza, Ponmeni, Kalavasal',
                'title': 'Motorcycle Theft from Hospital Parking near Vasan Eye Care',
                'category': 'Theft',
                'priority': 'Medium',
                'confidence': '88.3%',
                'status': 'Under Investigation',
                'fir_status': 'FIR Registered',
                'case_status': 'Investigation in Progress',
                'description': 'My Hero Splendor Plus motorcycle (TN 58 AB 4590) parked in the visitor parking area was stolen after the lock was broken using master keys.',
                'days_ago': 5, 'time': '14:20'
            },
            {
                'area': 'Kalavasal',
                'landmark': 'Canara Bank (Kalavasal)',
                'lat': '9.93109', 'lon': '78.09445',
                'address': 'By-Pass Road near Canara Bank, Kalavasal',
                'title': 'Bank ATM Skimming and Phishing Scam near Canara Bank',
                'category': 'Cybercrime',
                'priority': 'Medium',
                'confidence': '89.0%',
                'status': 'Under Investigation',
                'fir_status': 'Pending',
                'case_status': 'Not Assigned',
                'description': 'An ATM card skimming device was attached to the kiosk machine. An unauthorized withdrawal of Rs. 38,000 took place within 30 minutes of using the ATM.',
                'days_ago': 7, 'time': '11:15'
            },
            {
                'area': 'Kalavasal',
                'landmark': 'Sri E N T Hospital',
                'lat': '9.93144', 'lon': '78.09673',
                'address': '48A Pandian Nagar West, Kalavasal',
                'title': 'Shop Signboard Vandalism and Property Damage at By-Pass Road',
                'category': 'Vandalism',
                'priority': 'Medium',
                'confidence': '86.5%',
                'status': 'Assigned',
                'fir_status': 'Pending',
                'case_status': 'Not Assigned',
                'description': 'Miscreants pelted stones late at night breaking the glass facade of our medical store and damaging outdoor display panels.',
                'days_ago': 12, 'time': '01:50'
            },
            {
                'area': 'Kalavasal',
                'landmark': 'Kalavasal (Kalavasal) #2',
                'lat': '9.93113', 'lon': '78.09479',
                'address': 'Bus Stop Shelter, Kalavasal',
                'title': 'Lost Smart Phone on Public Bus at Kalavasal Bus Stop',
                'category': 'Theft',
                'priority': 'Low',
                'confidence': '85.4%',
                'status': 'Pending Review',
                'fir_status': 'Not Filed',
                'case_status': 'Not Assigned',
                'description': 'Lost my Samsung Galaxy A52 smartphone while boarding route bus 77 at Kalavasal bus shelter. Phone was switched off immediately.',
                'days_ago': 3, 'time': '08:45'
            },
            {
                'area': 'Kalavasal',
                'landmark': 'P.P. Chavadi',
                'lat': '9.93238', 'lon': '78.09306',
                'address': 'Theni Road, near P.P. Chavadi, Kalavasal',
                'title': 'Noise Pollution and Late Night Argument near P.P. Chavadi',
                'category': 'Other',
                'priority': 'Low',
                'confidence': '87.1%',
                'status': 'Resolved',
                'fir_status': 'Not Filed',
                'case_status': 'Closed',
                'description': 'Public nuisance and loud arguments between street vendors until 2 AM disturbing nearby residents. Police patrol resolved the matter.',
                'days_ago': 14, 'time': '23:30'
            },

            # === MATTUTHAVANI (HIGH CRIME REGION) ===
            {
                'area': 'Mattuthavani',
                'landmark': 'Omni Paerundhu Nilaiyam',
                'lat': '9.94536', 'lon': '78.15803',
                'address': 'Omni Bus Stand, Mattuthavani',
                'title': 'Gang Extortion and Weapon Threat at Omni Bus Stand',
                'category': 'Assault',
                'priority': 'High',
                'confidence': '97.2%',
                'status': 'FIR Registered',
                'fir_status': 'FIR Registered',
                'case_status': 'Charge Sheet Filed in Court',
                'description': 'Organized rowdy gang demanding illegal monthly extortion (maamool) from private travel operators at Omni bus stand. The gang brandished knives and threatened operators with dire consequences.',
                'days_ago': 1, 'time': '22:00'
            },
            {
                'area': 'Mattuthavani',
                'landmark': 'MGR Paerundhu Nilaiyam',
                'lat': '9.94383', 'lon': '78.15621',
                'address': 'MGR Integrated Bus Terminus, Platform 4, Mattuthavani',
                'title': 'Midnight Armed Robbery of Passenger near MGR Bus Terminus',
                'category': 'Theft',
                'priority': 'High',
                'confidence': '95.9%',
                'status': 'FIR Registered',
                'fir_status': 'FIR Registered',
                'case_status': 'Investigation in Progress',
                'description': 'Arrived on an outstation bus from Chennai at 1 AM. While walking toward the prepaid taxi stand, three men surrounded me in a dark corridor, held a knife to my neck, and took Rs. 28,000 cash and laptop bag.',
                'days_ago': 3, 'time': '01:15'
            },
            {
                'area': 'Mattuthavani',
                'landmark': 'Meen Angadi',
                'lat': '9.94272', 'lon': '78.15669',
                'address': 'Fish Market Complex, Mattuthavani',
                'title': 'Severe Physical Assault and Knife Attack near Meen Angadi',
                'category': 'Assault',
                'priority': 'High',
                'confidence': '96.1%',
                'status': 'FIR Registered',
                'fir_status': 'FIR Registered',
                'case_status': 'Accused Interrogated / Under Arrest',
                'description': 'Violent clash between two rival vendor factions inside the fish market. Knife was pulled out and one worker sustained deep incisions on the shoulder. Immediate police intervention required.',
                'days_ago': 5, 'time': '05:30'
            },
            {
                'area': 'Mattuthavani',
                'landmark': 'HP Petrol Bunk',
                'lat': '9.94445', 'lon': '78.15415',
                'address': 'Melur Main Road near HP Petrol Bunk, Mattuthavani',
                'title': 'Coordinated Chain Snatching with Bodily Injury near HP Petrol Bunk',
                'category': 'Theft',
                'priority': 'High',
                'confidence': '93.5%',
                'status': 'Under Investigation',
                'fir_status': 'FIR Registered',
                'case_status': 'Investigation in Progress',
                'description': 'While waiting for bus near HP petrol pump, two bike-borne men snatched gold thali chain (4.5 sovereigns) from my mother, causing her to fall and fracture her wrist.',
                'days_ago': 7, 'time': '20:30'
            },
            {
                'area': 'Mattuthavani',
                'landmark': 'Meenakshi Mission Hospital',
                'lat': '9.94848', 'lon': '78.16254',
                'address': 'Melur Road, near Meenakshi Mission Hospital, Mattuthavani',
                'title': 'Violent Kidnapping Attempt and Extortion near Meenakshi Mission Hospital',
                'category': 'Assault',
                'priority': 'High',
                'confidence': '98.0%',
                'status': 'FIR Registered',
                'fir_status': 'FIR Registered',
                'case_status': 'Court Trial / Hearing',
                'description': 'Four suspects in a white Scorpio attempted to forcibly drag a college student into their vehicle outside the hospital gates. Nearby public raised an alarm and suspects fled toward Melur highway.',
                'days_ago': 9, 'time': '18:15'
            },
            {
                'area': 'Mattuthavani',
                'landmark': 'MGR Paerundhu Nilaiyam',
                'lat': '9.94383', 'lon': '78.15621',
                'address': 'Two-Wheeler Stand, Mattuthavani Integrated Bus Stand',
                'title': 'Two-Wheeler Theft from Transit Commuter Stand at MGR Terminus',
                'category': 'Theft',
                'priority': 'Medium',
                'confidence': '89.2%',
                'status': 'Assigned',
                'fir_status': 'Pending',
                'case_status': 'Not Assigned',
                'description': 'My Bajaj Pulsar 150 (TN 59 BX 8912) parked at the official railway/bus commuter paid parking lot was stolen within 6 hours. Parking token was tampered with.',
                'days_ago': 4, 'time': '16:00'
            },
            {
                'area': 'Mattuthavani',
                'landmark': 'Omni Paerundhu Nilaiyam',
                'lat': '9.94536', 'lon': '78.15803',
                'address': 'Private Travels Counter, Mattuthavani',
                'title': 'Counterfeit Bus Ticket Scam and Fraud near Omni Bus Stand',
                'category': 'Fraud',
                'priority': 'Medium',
                'confidence': '88.7%',
                'status': 'Under Investigation',
                'fir_status': 'Pending',
                'case_status': 'Not Assigned',
                'description': 'Fake travel agent sold invalid sleeper tickets to a group of 8 passengers collecting Rs. 14,400 online, and switched off their phone when the bus arrived.',
                'days_ago': 11, 'time': '21:45'
            },
            {
                'area': 'Mattuthavani',
                'landmark': 'Poo Angadi',
                'lat': '9.94177', 'lon': '78.15202',
                'address': 'Flower Market, Mattuthavani',
                'title': 'Commercial Flower Stall Theft and Cash Box Break-in at Poo Angadi',
                'category': 'Theft',
                'priority': 'Medium',
                'confidence': '87.4%',
                'status': 'Assigned',
                'fir_status': 'Pending',
                'case_status': 'Not Assigned',
                'description': 'Wholesale flower stall tin sheet lock was dismantled overnight. Cash box containing daily market collections of Rs. 32,000 was stolen.',
                'days_ago': 13, 'time': '04:10'
            },
            {
                'area': 'Mattuthavani',
                'landmark': 'MGR Paerundhu Nilaiyam',
                'lat': '9.94383', 'lon': '78.15621',
                'address': 'Waiting Hall, MGR Bus Stand, Mattuthavani',
                'title': 'Misplaced Luggage and Travel Documents at MGR Terminus Platform',
                'category': 'Theft',
                'priority': 'Low',
                'confidence': '86.1%',
                'status': 'Pending Review',
                'fir_status': 'Not Filed',
                'case_status': 'Not Assigned',
                'description': 'A trolley suitcase containing clothes, degree certificates, and PAN card was accidentally left behind on the seating bench at Bay 3.',
                'days_ago': 2, 'time': '13:30'
            },
            {
                'area': 'Mattuthavani',
                'landmark': 'Preethi Hospital',
                'lat': '9.94724', 'lon': '78.15795',
                'address': '120 Feet Road, near Preethi Hospital, Mattuthavani',
                'title': 'Fare Overcharging Dispute and Verbal Argument near Preethi Hospital',
                'category': 'Other',
                'priority': 'Low',
                'confidence': '85.0%',
                'status': 'Resolved',
                'fir_status': 'Not Filed',
                'case_status': 'Closed',
                'description': 'Auto driver demanded triple fare late at night, leading to an aggressive verbal altercation outside the hospital. Reconciled amicably.',
                'days_ago': 15, 'time': '22:40'
            },

            # === VILLAPURAM (MEDIUM CRIME REGION) ===
            {
                'area': 'Villapuram',
                'landmark': 'Amirthamal Hospital',
                'lat': '9.90187', 'lon': '78.12084',
                'address': 'Aruppukottai Salai near Amirthamal Hospital, Villapuram',
                'title': 'Gold Chain Snatching by Motorcycle Assailants near Amirthamal Hospital',
                'category': 'Theft',
                'priority': 'High',
                'confidence': '93.2%',
                'status': 'FIR Registered',
                'fir_status': 'FIR Registered',
                'case_status': 'Investigation in Progress',
                'description': 'Two youngsters on a black motorcycle snatched a 3-sovereign gold chain from a nurse returning home from hospital duty. Suspects sped toward Ring Road.',
                'days_ago': 3, 'time': '20:15'
            },
            {
                'area': 'Villapuram',
                'landmark': 'Meenakshi Sugam Hospital',
                'lat': '9.89457', 'lon': '78.11955',
                'address': 'Vasuki Street, Ganapathy Nagar, Villapuram',
                'title': 'Street Robbery and Threat with Knife near Meenakshi Sugam Hospital',
                'category': 'Assault',
                'priority': 'High',
                'confidence': '91.8%',
                'status': 'Under Investigation',
                'fir_status': 'FIR Registered',
                'case_status': 'Investigation in Progress',
                'description': 'Pedestrian returning from grocery shop was cornered by two individuals armed with a kitchen knife, demanding wallet and phone.',
                'days_ago': 9, 'time': '21:50'
            },
            {
                'area': 'Villapuram',
                'landmark': 'Vetri Cinemas Madurai',
                'lat': '9.90043', 'lon': '78.12025',
                'address': 'Avaniyapuram Main Road, near Vetri Cinemas, Villapuram',
                'title': 'Two-Wheeler Theft from Residential Street near Vetri Cinemas',
                'category': 'Theft',
                'priority': 'Medium',
                'confidence': '88.9%',
                'status': 'Assigned',
                'fir_status': 'Pending',
                'case_status': 'Not Assigned',
                'description': 'My TVS Jupiter scooter (TN 59 CP 3341) parked outside my house gate overnight was stolen. Handlebar lock was broken.',
                'days_ago': 5, 'time': '02:00'
            },
            {
                'area': 'Villapuram',
                'landmark': 'State Bank of India (Villapuram)',
                'lat': '9.90407', 'lon': '78.11842',
                'address': 'Housing Board Main Road, Villapuram',
                'title': 'Unauthorized Online Cyber Debit Card Transaction at Villapuram',
                'category': 'Cybercrime',
                'priority': 'Medium',
                'confidence': '89.5%',
                'status': 'Under Investigation',
                'fir_status': 'Pending',
                'case_status': 'Not Assigned',
                'description': 'Rs. 24,500 was debited in multiple unauthorized micro-transactions through an international merchant gateway without OTP notification.',
                'days_ago': 6, 'time': '15:20'
            },
            {
                'area': 'Villapuram',
                'landmark': 'Hindustan Petroleum Corporation Limited',
                'lat': '9.89842', 'lon': '78.11973',
                'address': 'Aruppukottai Salai, Villapuram',
                'title': 'Commercial Store Vandalism and Shoplifting near Aruppukottai Salai',
                'category': 'Vandalism',
                'priority': 'Medium',
                'confidence': '86.4%',
                'status': 'Assigned',
                'fir_status': 'Pending',
                'case_status': 'Not Assigned',
                'description': 'Local youth created a ruckus at our grocery supermarket, damaged checkout computer screen, and walked away with energy drinks and groceries.',
                'days_ago': 8, 'time': '18:40'
            },
            {
                'area': 'Villapuram',
                'landmark': 'Padma Theatre Bus Stop',
                'lat': '9.89561', 'lon': '78.11797',
                'address': 'Aruppukottai Road, near Padma Theatre, Villapuram',
                'title': 'Lost College Examination Hall Ticket and Purse near Padma Theatre',
                'category': 'Theft',
                'priority': 'Low',
                'confidence': '86.0%',
                'status': 'Pending Review',
                'fir_status': 'Not Filed',
                'case_status': 'Not Assigned',
                'description': 'Left a small purse with university identity card, exam hall ticket, and Rs. 500 inside an autorickshaw boarded near Padma Theatre stop.',
                'days_ago': 4, 'time': '09:10'
            },
            {
                'area': 'Villapuram',
                'landmark': 'MMC Colony Bus Stop',
                'lat': '9.89282', 'lon': '78.11699',
                'address': 'MMC Colony, Villapuram',
                'title': 'Late Night Loudspeaker Noise Nuisance Complaint near Mappalayam',
                'category': 'Other',
                'priority': 'Low',
                'confidence': '85.2%',
                'status': 'Resolved',
                'fir_status': 'Not Filed',
                'case_status': 'Closed',
                'description': 'High volume music played beyond permissible night hours at an empty plot disturbing school students and senior citizens.',
                'days_ago': 12, 'time': '23:15'
            },

            # === NELPETTAI (LOW CRIME REGION) ===
            {
                'area': 'Nelpettai',
                'landmark': 'Nelpettai Market',
                'lat': '9.92180', 'lon': '78.12435',
                'address': '11-A, E Napalayam St, Nelpettai, Madurai Main',
                'title': 'Lost Wallet Containing Aadhar Card and Cash near Nelpettai Market',
                'category': 'Theft',
                'priority': 'Low',
                'confidence': '87.5%',
                'status': 'Pending Review',
                'fir_status': 'Not Filed',
                'case_status': 'Not Assigned',
                'description': 'Lost leather wallet containing original Aadhar card, voter ID, and cash Rs. 1,200 while purchasing vegetables at Nelpettai Market.',
                'days_ago': 2, 'time': '10:30'
            },
            {
                'area': 'Nelpettai',
                'landmark': 'Simmakkal Bus Stop',
                'lat': '9.92428', 'lon': '78.12102',
                'address': 'Simmakkal Circle, near Nelpettai',
                'title': 'Loudspeaker Disturbance during Festival near Simmakkal Bus Stop',
                'category': 'Other',
                'priority': 'Low',
                'confidence': '85.7%',
                'status': 'Resolved',
                'fir_status': 'Not Filed',
                'case_status': 'Closed',
                'description': 'Festival organizers placed box amplifiers on the road margin causing decibel violations. Resolved upon verbal warning.',
                'days_ago': 6, 'time': '21:00'
            },
            {
                'area': 'Nelpettai',
                'landmark': 'Karuppana Sami Temple',
                'lat': '9.92300', 'lon': '78.12403',
                'address': '51 East Marat Street, near Nelpettai',
                'title': 'Minor Verbal Argument between Vegetable Vendors at Nelpettai Market',
                'category': 'Other',
                'priority': 'Low',
                'confidence': '86.4%',
                'status': 'Resolved',
                'fir_status': 'Not Filed',
                'case_status': 'Closed',
                'description': 'Dispute regarding stall spacing on pavement between two neighboring fruit sellers. Resolved amicably without violence.',
                'days_ago': 10, 'time': '07:30'
            },
            {
                'area': 'Nelpettai',
                'landmark': 'Arun Hospital Madurai',
                'lat': '9.92103', 'lon': '78.12576',
                'address': 'Munichalai Road, near Arun Hospital, Nelpettai',
                'title': 'Stolen Bicycle from Outside Shop on Munichalai Road',
                'category': 'Theft',
                'priority': 'Medium',
                'confidence': '87.9%',
                'status': 'Assigned',
                'fir_status': 'Pending',
                'case_status': 'Not Assigned',
                'description': 'Hercules gear bicycle parked outside the medical shop for 20 minutes was taken away by an unidentified youth.',
                'days_ago': 7, 'time': '17:15'
            },
            {
                'area': 'Nelpettai',
                'landmark': 'Adyar Ananda Bhavan A2B Veg Restaurant - Vilakuthoon Madurai',
                'lat': '9.91768', 'lon': '78.12386',
                'address': 'Kamarajar Salai, near Vilakuthoon and Nelpettai',
                'title': 'Attempted Pickpocketing with Small Blade near Kamarajar Salai',
                'category': 'Theft',
                'priority': 'High',
                'confidence': '92.0%',
                'status': 'Under Investigation',
                'fir_status': 'FIR Registered',
                'case_status': 'Investigation in Progress',
                'description': 'Suspect attempted to slice through trouser pocket to steal purse in crowded bazaar. Caught red-handed by public and handed over to police patrol.',
                'days_ago': 8, 'time': '19:10'
            },
        ]

        # 3. Create the complaints
        current_count = Complaint.objects.count()
        today = datetime.now()

        created_count = 0
        for i, spec in enumerate(complaints_specs):
            # Assign in round-robin across david@gmail.com, kabes@gmail.com, madhu@gmail.com
            citizen = citizens[i % len(citizens)]

            incident_dt = today - timedelta(days=spec['days_ago'])
            incident_date_str = incident_dt.strftime('%Y-%m-%d')
            created_at_str = incident_dt.strftime('%Y-%m-%d %H:%M:%S')

            # Route to closest police station
            matched_station, dist_km, _ = find_jurisdiction_station(
                complaint_lat=spec['lat'],
                complaint_lon=spec['lon'],
                city='Madurai',
                address=spec['address'],
                stations=stations
            )

            st_id = matched_station.station_id if matched_station else 'PS-001'
            st_name = matched_station.name if matched_station else 'Primary Police Station'

            current_count += 1
            cid = f"CMP-{current_count:03d}"

            # Make sure ID is unique
            while Complaint.objects.filter(complaint_id=cid).exists():
                current_count += 1
                cid = f"CMP-{current_count:03d}"

            comp = Complaint.objects.create(
                complaint_id=cid,
                citizen_name=citizen.name,
                citizen_email=citizen.email,
                citizen_phone=citizen.phone,
                title=spec['title'],
                category=spec['category'],
                description=spec['description'],
                incident_date=incident_date_str,
                incident_time=spec['time'],
                address=spec['address'],
                area=spec['area'],
                street=spec['address'],
                city='Madurai',
                district='Madurai',
                pincode='625001',
                latitude=spec['lat'],
                longitude=spec['lon'],
                landmark=spec['landmark'],
                evidence='',
                assigned_station_id=st_id,
                assigned_station_name=st_name,
                assigned_officer_id='officer.a@tnpolice.gov.in' if spec['status'] != 'Pending Review' else '',
                assigned_officer_name='Sub Inspector' if spec['status'] != 'Pending Review' else '',
                assigned_by_inspector='Station In-Charge Inspector' if spec['status'] != 'Pending Review' else '',
                assigned_date=incident_date_str if spec['status'] != 'Pending Review' else '',
                status=spec['status'],
                fir_status=spec['fir_status'],
                case_status=spec['case_status'],
                ai_duplicate_flag='Unique',
                ai_similarity_score='8%',
                ai_priority=spec['priority'],
                ai_priority_confidence=spec['confidence'],
                created_at=created_at_str
            )

            created_count += 1
            self.stdout.write(
                f"[{spec['area'].upper()}] {comp.complaint_id} | {spec['priority']} Priority | {citizen.email} | {comp.title[:45]}..."
            )

        self.stdout.write(self.style.SUCCESS(
            f"\nSuccessfully created {created_count} complaints:\n"
            f"- Kalavasal: 10 complaints (HIGH crime rate: 5 High, 3 Medium, 2 Low)\n"
            f"- Mattuthavani: 10 complaints (HIGH crime rate: 5 High, 3 Medium, 2 Low)\n"
            f"- Villapuram: 7 complaints (MEDIUM crime rate: 2 High, 3 Medium, 2 Low)\n"
            f"- Nelpettai: 5 complaints (LOW crime rate: 1 High, 1 Medium, 3 Low)\n"
            f"Assigned across citizens: {[c.email for c in citizens]}"
        ))
