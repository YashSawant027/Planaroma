from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Guest, Event, RSVP

@api_view(['POST'])
def update_guest_rsvp(request):
    """
    Updates the RSVP status for a given guest and event.
    Expected payload:
    {
        "guest_id": 1,
        "event_name": "Wedding Ceremony",
        "status": "attending"
    }
    """
    guest_id = request.data.get('guest_id')
    event_name = request.data.get('event_name')
    new_status = request.data.get('status')

    if not all([guest_id, new_status]):
        return Response({"error": "guest_id and status are required."}, status=status.HTTP_400_BAD_REQUEST)

    guest = get_object_or_404(Guest, id=guest_id)
    
    # If event_name is provided, filter by it, otherwise just get the first RSVP or a specific one.
    # Usually, if we want to be safe, we require event_name, but we can default if they only have 1 event.
    rsvps = RSVP.objects.filter(guest=guest)
    if event_name:
        rsvps = rsvps.filter(event__name__icontains=event_name)
    
    if not rsvps.exists():
        return Response({"error": f"No RSVP found for guest {guest.name} and event {event_name}."}, status=status.HTTP_404_NOT_FOUND)

    # Update all matching RSVPs (usually just 1)
    updated_count = 0
    for rsvp in rsvps:
        rsvp.status = new_status
        rsvp.save()
        updated_count += 1

    return Response({
        "success": True, 
        "message": f"Updated {updated_count} RSVP(s) for {guest.name} to {new_status}."
    })


@api_view(['POST'])
def add_plus_one(request):
    """
    Adds a specified number of plus ones to a guest's RSVP.
    Expected payload:
    {
        "guest_id": 1,
        "count": 1,
        "event_name": "Wedding Ceremony"  # optional
    }
    """
    guest_id = request.data.get('guest_id')
    count = request.data.get('count', 1)
    event_name = request.data.get('event_name')

    if not guest_id:
        return Response({"error": "guest_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        count = int(count)
    except ValueError:
        return Response({"error": "count must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

    guest = get_object_or_404(Guest, id=guest_id)
    rsvps = RSVP.objects.filter(guest=guest)
    if event_name:
        rsvps = rsvps.filter(event__name__icontains=event_name)
    
    if not rsvps.exists():
        return Response({"error": f"No RSVP found for guest {guest.name}."}, status=status.HTTP_404_NOT_FOUND)

    updated_count = 0
    for rsvp in rsvps:
        rsvp.plus_ones += count
        rsvp.save()
        updated_count += 1

    return Response({
        "success": True, 
        "message": f"Added {count} plus one(s) for {guest.name}."
    })
