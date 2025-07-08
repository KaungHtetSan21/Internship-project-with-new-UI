from datetime import date, timedelta
from .models import Item

def expiry_alert_items(request):
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        if request.user.userprofile.role == 'pharmacist':
            today = date.today()
            threshold_date = today + timedelta(days=90)
            expiring_items = Item.objects.filter(exp_date__lte=threshold_date, exp_date__gte=today).order_by('exp_date')
            return {'expiring_items': expiring_items}
    return {}