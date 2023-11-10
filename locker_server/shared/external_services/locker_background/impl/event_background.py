from django.db import connection


from locker_server.shared.external_services.locker_background.background import LockerBackground


class EventBackground(LockerBackground):
    def create(self, **data):
        from locker_server.containers.containers import event_service
        try:
            event_service.create_new_event(**data)
        except Exception as e:
            self.log_error(func_name="create")
        finally:
            if self.background:
                connection.close()

    def create_by_team_ids(self, team_ids, **data):
        from locker_server.containers.containers import event_service
        try:
            if team_ids:
                event_service.create_new_event_by_multiple_teams(team_ids, **data)
            else:
                self.create(**data)
        except Exception as e:
            self.log_error(func_name="create_by_team_ids")
        finally:
            if self.background:
                connection.close()

    def create_by_enterprise_ids(self, enterprise_ids, **data):
        from locker_server.containers.containers import event_service
        try:
            if enterprise_ids:
                event_service.create_new_event_by_multiple_teams(enterprise_ids, **data)
            else:
                self.create(**data)
        except Exception as e:
            self.log_error(func_name="create_by_enterprise_ids")
        finally:
            if self.background:
                connection.close()

    def create_by_ciphers(self, ciphers, **data):
        from locker_server.containers.containers import event_service
        try:
            if ciphers:
                event_service.create_new_event_by_ciphers(ciphers, **data)
            else:
                self.create(**data)
        except Exception as e:
            self.log_error(func_name="create_by_ciphers")
        finally:
            if self.background:
                connection.close()

