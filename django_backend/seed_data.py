import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from events.models import Event, Guest, RSVP

def run():
    wedding_date = timezone.now() + timedelta(days=30)
    event, _ = Event.objects.get_or_create(
        name="Wedding",
        defaults={"date": wedding_date, "description": "The main wedding ceremony."}
    )

    rehearsal_date = timezone.now() + timedelta(days=29)
    event2, _ = Event.objects.get_or_create(
        name="Rehearsal Dinner",
        defaults={"date": rehearsal_date, "description": "Dinner for close family."}
    )

    guests_data = [
        {"name": "Rahul Sharma", "email": "rahul.s@example.com"},
        {"name": "Rahul Verma", "email": "rahul.v@example.com"},
        {"name": "Priya Singh", "email": "priya@example.com"},
        {"name": "Amit Kumar", "email": "amit@example.com"}
    ]
    
    guests = []
    for g in guests_data:
        guest, _ = Guest.objects.get_or_create(email=g["email"], defaults={"name": g["name"]})
        guests.append(guest)
        
    RSVP.objects.get_or_create(guest=guests[2], event=event, defaults={"status": "attending", "plus_ones": 1})
    RSVP.objects.get_or_create(guest=guests[3], event=event, defaults={"status": "declined"})
    RSVP.objects.get_or_create(guest=guests[0], event=event, defaults={"status": "pending"})
    RSVP.objects.get_or_create(guest=guests[1], event=event, defaults={"status": "pending"})

if __name__ == "__main__":
    run()
