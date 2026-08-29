# pyrefly: ignore [missing-import]
from django.contrib import admin
from .models import (
    User, PoliceStation, Location, Complaint, Alert, SOS, MissingPerson,
    LostFound, FIR, Case, Evidence, Accused, Feedback
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'official_email', 'role', 'rank', 'station_name', 'is_verified', 'approval_status')
    search_fields = ('name', 'email', 'official_email', 'station_name')
    list_filter = ('role', 'is_verified', 'approval_status')


@admin.register(PoliceStation)
class PoliceStationAdmin(admin.ModelAdmin):
    list_display = ('station_id', 'name', 'station_type', 'district', 'contact', 'incharge_inspector_name')
    search_fields = ('station_id', 'name', 'district')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'location_type')
    search_fields = ('name', 'location_type')


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('complaint_id', 'title', 'category', 'area', 'assigned_station_name', 'status', 'ai_duplicate_flag')
    search_fields = ('complaint_id', 'title', 'citizen_name', 'assigned_station_name')
    list_filter = ('status', 'category', 'ai_duplicate_flag')


admin.site.register(Alert)
admin.site.register(SOS)
admin.site.register(MissingPerson)
admin.site.register(LostFound)
admin.site.register(FIR)
admin.site.register(Case)
admin.site.register(Evidence)
admin.site.register(Accused)
admin.site.register(Feedback)