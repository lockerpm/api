from django.db.models import F

from shared.utils.app import now
from shared.constants.emergency_access import *
from cystack_models.models.emergency_access.emergency_access import EmergencyAccess


def emergency_access_auto_approve():
    current_time = now()
    EmergencyAccess.objects.filter(
        status=EMERGENCY_ACCESS_STATUS_RECOVERY_INITIATED,
        recovery_initiated_date__lte=current_time - F('wait_time_days') * 86400
    ).update(status=EMERGENCY_ACCESS_STATUS_RECOVERY_APPROVED)
