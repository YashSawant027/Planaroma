from django.urls import path
from .views import update_guest_rsvp, add_plus_one

urlpatterns = [
    path('rsvp/update/', update_guest_rsvp, name='update_guest_rsvp'),
    path('rsvp/plus-one/', add_plus_one, name='add_plus_one'),
]
