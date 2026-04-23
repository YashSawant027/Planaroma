from django.db import models

class Guest(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

class Event(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateTimeField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class RSVP(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('attending', 'Attending'),
        ('declined', 'Declined'),
    ]
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='rsvps')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    plus_ones = models.IntegerField(default=0)

    class Meta:
        unique_together = ('guest', 'event')

    def __str__(self):
        return f"{self.guest.name} - {self.event.name}: {self.status}"
