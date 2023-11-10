import io
import json
import traceback
from typing import Dict, List

import django_rq
import xlsxwriter

from locker_server.core.entities.enterprise.member.enterprise_member import EnterpriseMember
from locker_server.core.entities.event.event import Event
from locker_server.core.repositories.event_repository import EventRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.external_services.locker_background.impl import NotifyBackground
from locker_server.shared.external_services.s3.s3_service import s3_service
from locker_server.shared.log.cylog import CyLog
from locker_server.shared.utils.app import now, convert_readable_date


class EventService:
    """
    This class represents Use Cases related Event
    """

    def __init__(self, event_repository: EventRepository, user_repository: UserRepository):
        self.event_repository = event_repository
        self.user_repository = user_repository

    def list_events(self, **filters) -> List[Event]:
        return self.event_repository.list_events(**filters)

    def create_new_event(self, **data) -> Event:
        return self.event_repository.create_new_event(**data)

    def create_new_event_by_multiple_teams(self, team_ids: list, **data):
        return self.event_repository.create_new_event_by_multiple_teams(team_ids, **data)

    def create_new_event_by_ciphers(self, ciphers, **data):
        return self.event_repository.create_new_event_by_ciphers(ciphers, **data)

    def create_multiple_by_enterprise_members(self, member_events_data):
        return self.event_repository.create_multiple_by_enterprise_members(member_events_data)

    @staticmethod
    def normalize_enterprise_activity(activity_logs: List[Event], users_data_dict: Dict, use_html: bool = True) -> List:
        """
        Map activity log user_id to users data
        :param activity_logs:
        :param users_data_dict:
        :param use_html:
        :return:
        """
        logs = []
        for activity_log in activity_logs:
            acting_user_id = activity_log.acting_user_id
            user_id = activity_log.user_id
            acting_user_data = users_data_dict.get(acting_user_id)
            user_data = users_data_dict.get(user_id)
            log = activity_log.get_activity_log_data()
            log["acting_user"] = {
                "name": acting_user_data.get("full_name"),
                "email": acting_user_data.get("email"),
                "username": acting_user_data.get("username"),
                "avatar": acting_user_data.get("avatar"),
            } if acting_user_data else {"name": "System", "email": None, "username": "System", "avatar": None}
            log["user"] = {
                "name": user_data.get("full_name"),
                "email": user_data.get("email"),
                "username": user_data.get("username"),
                "avatar": user_data.get("avatar"),
            } if user_data else None
            metadata = log.get("metadata", {})
            metadata.update({"user_email": user_data.get("email") if user_data else "Former user"})
            activity_log.metadata = metadata
            log["description"] = activity_log.get_description(use_html=use_html)
            # log.pop("metadata", None)
            logs.append(log)
        return logs

    def export_enterprise_activity(self, enterprise_member: EnterpriseMember, activity_logs, cc_emails=None, **kwargs):
        django_rq.enqueue(
            self.export_enterprise_activity_job, enterprise_member, activity_logs, cc_emails,
            kwargs.get("from"), kwargs.get("to")
        )

    def export_enterprise_activity_job(self, enterprise_member, activity_logs, cc_emails=None,
                                       from_param=None, to_param=None):
        current_time = now()
        filename = "activity_logs_{}".format(convert_readable_date(current_time, "%Y%m%d"))

        # Write to xlsx file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        title = ["Action", "Actor", "Time", "IP Address"]
        worksheet.write_row(0, 0, title)
        row_index = 2
        for log in activity_logs:
            row = [
                log.get("description", {}).get("en"),
                log.get("acting_user", {}).get("email") if log.get("acting_user") else "",
                convert_readable_date(log.get("creation_date")),
                log.get("ip_address")
            ]
            worksheet.write_row(row_index, 0, row)
            row_index += 1
        workbook.close()
        output.seek(0)

        # Upload to S3
        s3_path = f"support/tmp/activity/{enterprise_member.enterprise.enterprise_id}/{filename}.xlsx"
        s3_service.upload_bytes_object(key=s3_path, io_bytes=output)

        # Close IO Stream
        output.close()

        download_url = s3_service.gen_one_time_url(file_path=s3_path, **{"expired": 900})
        CyLog.debug(**{"message": f"Exported to {download_url}"})

        # Sending mail
        NotifyBackground(background=False).notify_enterprise_export(data={
            "user_ids": [enterprise_member.user.user_id],
            "cc": cc_emails,
            "attachments": [{
                "url": download_url,
                "name": f"{filename}.xlsx"
            }],
            "org_name": enterprise_member.enterprise.name,
            "start_date": from_param,
            "end_date": to_param
        })

    def export_enterprise_activity_job_local(self, activity_logs):
        try:
            current_time = now()
            filename = "activity_logs_{}".format(convert_readable_date(current_time, "%Y%m%d"))
            # Write to xlsx file
            rows = list()
            for log in activity_logs:
                row = "{},{},{},{}".format(
                    log.get("description", {}).get("en"),
                    log.get("acting_user", {}).get("email") if log.get("acting_user") else "",
                    convert_readable_date(log.get("creation_date")),
                    log.get("ip_address")
                )
                rows.append(row)
            with open(f'{filename}.log', 'w', encoding="utf-8") as f:
                for row in rows:
                    f.write(f"{row}\n")
        except Exception as e:
            tb = traceback.format_exc()
            CyLog.error(**{"message": f"[!] Exception when export enterprise activity log: {tb}"})
        finally:
            pass

    def statistic_login_by_time(self, enterprise_id: str, user_ids: List[int], from_param: float,
                                to_param: float) -> Dict:
        return self.event_repository.statistic_login_by_time(
            team_id=enterprise_id,
            user_ids=user_ids,
            from_param=from_param,
            to_param=to_param
        )
