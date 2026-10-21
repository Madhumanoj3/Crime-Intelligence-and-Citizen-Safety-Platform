from django.urls import path
from . import views

urlpatterns = [
    # Auth & Landing
    path('', views.register, name='register'),
    path('home/', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/citizen/', views.register, name='register_citizen'),
    path('register/police/', views.police_register, name='police_register'),

    # Citizen Panel
    path('citizen/dashboard/', views.citizen_dashboard, name='citizen_dashboard'),
    path('citizen/complaint/new/', views.complaint_form, name='complaint_form'),
    path('citizen/complaints/', views.complaints, name='complaints'),
    path('citizen/complaint/detail/', views.complaint_detail, name='complaint_detail'),
    path('citizen/sos/', views.sos, name='sos'),
    path('citizen/missing-person/', views.missing_person, name='missing_person'),
    path('citizen/lost-found/', views.lost_found, name='lost_found'),
    path('citizen/community-alerts/', views.community_alerts, name='community_alerts'),

    # Inspector Panel (Station In-Charge)
    path('inspector/dashboard/', views.inspector_dashboard, name='inspector_dashboard'),
    path('inspector/monitoring/', views.inspector_monitoring, name='inspector_monitoring'),

    # Police Officer Panel (Investigating Officer)
    path('officer/dashboard/', views.officer_dashboard, name='officer_dashboard'),

    # Common Police Routes (Router & Tools)
    path('police/dashboard/', views.police_dashboard, name='police_dashboard'),
    path('police/complaints/', views.police_complaints, name='police_complaints'),
    path('police/fir/', views.fir, name='fir'),
    path('police/cases/', views.cases, name='cases'),
    path('police/evidence/', views.evidence, name='evidence'),
    path('police/accused/', views.accused, name='accused'),
    path('police/sos/', views.police_sos, name='police_sos'),
    path('police/crime-intelligence/', views.crime_intelligence, name='crime_intelligence'),
    path('api/hotspots/', views.hotspots_api, name='hotspots_api'),

    # Admin Panel (Station & User Hierarchy)
    path('admin-panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.users, name='users'),
    path('admin-panel/police-stations/', views.police_stations, name='police_stations'),
    path('admin-panel/alerts/', views.admin_alerts, name='admin_alerts'),

    # Feedback
    path('feedback/', views.feedback, name='feedback'),
    path('thankyou/', views.thankyou, name='thankyou'),
    path('setup-initial-data/', views.setup_initial_data, name='setup_initial_data'),
]