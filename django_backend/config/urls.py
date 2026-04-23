from django.contrib import admin
from django.urls import path, include
from messaging.views import webhook_email_status

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/events/', include('events.urls')),
    path('api/webhooks/email/status/', webhook_email_status),
]
