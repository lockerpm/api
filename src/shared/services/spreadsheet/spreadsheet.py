import ast
import gspread
import requests
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from core.settings import CORE_CONFIG
from shared.constants.transactions import PLAN_TYPE_PM_PREMIUM, PLAN_TYPE_PM_FREE
from shared.log.cylog import CyLog
from shared.utils.app import now


API_USERS = "{}/micro_services/users".format(settings.GATEWAY_API)
HEADERS = {
    "User-agent": "CyStack Locker",
    "Authorization": settings.MICRO_SERVICE_USER_AUTH
}


class LockerSpreadSheet:
    def __init__(self, url=settings.GOOGLE_SHEET_FEEDBACK_URL):
        self.url = url
        self.client = self._init_client(cred=ast.literal_eval(str(settings.GOOGLE_SHEET_FEEDBACK_SERVICE_ACCOUNT)))
        self.user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()

    def _init_client(self, cred):
        scopes = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        client = gspread.service_account_from_dict(cred, scopes=scopes)
        return client

    def get_email_survey_sheet(self):
        sheet = self.client.open_by_url(self.url).worksheet("Email from survey")
        return sheet

    def upgrade_survey_email(self):
        current_time = now()
        current_time_str = datetime.fromtimestamp(current_time).strftime("%d-%b-%Y")
        # Get emails from sheet
        sheet = self.get_email_survey_sheet()
        all_records = sheet.get_values()[1:]
        not_upgraded_records = [record for record in all_records if record[5] != '1']
        emails = [record[1] for record in not_upgraded_records if record[1] != '']

        # Get user data from Gateway
        users_data = self.get_users_data(emails=emails)
        if not users_data:
            return

        # Loop: Upgrade user
        for user_data in users_data:
            user = self.get_user_obj(user_id=user_data["id"])
            # Not found Locker account => continue
            if not user or user.activated is False:
                continue
            # If current plan of the user is not Free => continue
            current_plan = self.user_repository.get_current_plan(user=user)
            if current_plan.get_plan_type_alias() != PLAN_TYPE_PM_FREE:
                continue

            # Upgrade user to Premium
            self.user_repository.update_plan(user=user, plan_type_alias=PLAN_TYPE_PM_PREMIUM, scope=settings.SCOPE_PWD_MANAGER, **{
                "start_period": current_time, "end_period": current_time + 365 * 86400
            })
            # Send mail here
            # CHANGE LATER ...

            # Update sheet
            email_cells = sheet.findall(user_data["email"])
            for cell in email_cells:
                row = cell.row
                # Updated Date, Create Locker account, Upgrade to Premium
                sheet.update_cell(row, 4, current_time_str)
                sheet.update_cell(row, 5, '1')
                sheet.update_cell(row, 6, '1')

    @staticmethod
    def get_users_data(emails):
        users_res = requests.post(url=API_USERS, headers=HEADERS, json={"emails": emails})
        if users_res.status_code != 200:
            CyLog.error(**{"message": "[LockerSpreadSheet] Get users from Gateway error: {} {}".format(
                users_res.status_code, users_res.text
            )})
            return
        users_data = users_res.json()
        return users_data

    def get_user_obj(self, user_id):
        try:
            user = self.user_repository.get_by_id(user_id=user_id)
            return user
        except ObjectDoesNotExist:
            return None
