import contextvars
import jwt

from django.conf import settings
from django.utils.encoding import smart_text
from rest_framework.authentication import get_authorization_header

from cystack_models.models.users.users import User
from shared.constants.token import TOKEN_PREFIX


# The context var represents the database alias in the settings
context_var = contextvars.ContextVar("DB", default='default')


def set_current_db_name(db):
    context_var.set(db)


def get_current_db_name():
    return context_var.get()


class TenantDBMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        return response

    def process_request(self, request):
        # Get user_id and enterprise of user
        user_id = self.decode_user_id(request)
        user = User.retrieve_or_create(user_id=user_id)
        enterprise_member = user.enterprise_members.first()
        if not enterprise_member:
            return None
        enterprise = enterprise_member.enterprise
        print("User_id: ", user_id, enterprise)
        # TODO: Check enterprise has a tenant db?
        if enterprise.id in [""]:
            db = f'locker_tenant_{enterprise.id}'
            context_var.set(db)

        # TODO: Handle /micro_services: MS payments, etc...

    def decode_user_id(self, request):
        token_value = self.get_auth_token(request)
        if token_value is None:
            return None
        if token_value.startswith(TOKEN_PREFIX):
            token_value = token_value[len(TOKEN_PREFIX):]

        try:
            payload = jwt.decode(token_value, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id', None)

            # Get profile in token
            user_id = int(user_id)
            return user_id
        except (jwt.InvalidSignatureError, jwt.DecodeError, jwt.InvalidAlgorithmError, ValueError):
            return None

    @staticmethod
    def get_auth_token(request):
        try:
            auth = get_authorization_header(request).split()
            valid_auth_header_prefix = ["bearer"]
            if not auth:
                return None

            # Check auth_header_prefix is `Bearer` token?
            if smart_text(auth[0].lower()) not in valid_auth_header_prefix:
                return None
            if len(auth) != 2:
                return None
            token = auth[1].decode('utf-8')
            return token  # Having `cs.`
        except (ValueError, KeyError, AttributeError):
            return None
