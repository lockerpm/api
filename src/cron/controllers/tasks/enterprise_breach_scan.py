from cystack_models.models.enterprises.enterprises import Enterprise
from shared.services.hibp.hibp_service import HibpService


def enterprise_breach_scan():
    enterprises = Enterprise.objects.filter(locked=False)
    for enterprise in enterprises:
        members = enterprise.enterprise_members.filter(is_activated=True, user__is_leaked=False).select_related('user')
        for member in members:
            user = member.user
            email = user.get_from_cystack_id().get("email")
            if email:
                hibp_check = HibpService().check_breach(email=email)
                if hibp_check:
                    user.is_leaked = True
                    user.save()
