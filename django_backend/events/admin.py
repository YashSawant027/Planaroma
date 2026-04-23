from django.contrib import admin
from .models import Guest, Event, RSVP

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone')
    search_fields = ('name', 'email')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'description')
    search_fields = ('name',)

@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ('guest', 'event', 'status', 'plus_ones')
    list_filter = ('status', 'event')
    search_fields = ('guest__name', 'event__name')
