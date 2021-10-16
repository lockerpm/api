from django.db.models import Count

from shared.utils.app import now
from cystack_models.models.users.user_refresh_tokens import UserRefreshToken


def delete_refresh_token():
    # The refresh tokens will be expired after 30 days
    expired_refresh_tokens = UserRefreshToken.objects.filter(
        created_time__lte=now() - 30 * 86400
    ).values_list('id', flat=True)
    UserRefreshToken.objects.filter(id__in=expired_refresh_tokens).delete()
