from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from messaging.models import MessageLog

@csrf_exempt
def webhook_email_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            provider_msg_id = data.get('provider_message_id')
            status = data.get('status')
            
            if not provider_msg_id or not status:
                return JsonResponse({'error': 'Missing required fields'}, status=400)
                
            try:
                log = MessageLog.objects.get(provider_message_id=provider_msg_id)
                log.status = status.lower()
                log.save()
                return JsonResponse({'message': 'Status updated successfully'})
            except MessageLog.DoesNotExist:
                return JsonResponse({'error': 'MessageLog not found'}, status=404)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
