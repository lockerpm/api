import ast
import firebase_admin
from firebase_admin import credentials

from django.conf import settings


credentials_json_data = ast.literal_eval(str(settings.FCM_CRED_SERVICE_ACCOUNT))

cred = credentials.Certificate(credentials_json_data)
default_app = firebase_admin.initialize_app(cred)
