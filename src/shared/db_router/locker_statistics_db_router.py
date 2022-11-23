# class LockerStatisticsDBRouter:
#     """
#     A router to control all database operations on models in the
#     locker_statistic application.
#     """
#     route_app_labels = {
#         'locker_statistic': 'locker_statistics_db'
#     }
#
#     def db_for_read(self, model, **hints):
#         """
#         Attempts to read locker_statistic models go to locker_statistics_db.
#         """
#         if model._meta.app_label in self.route_app_labels:
#             return self.route_app_labels.get(model._meta.app_label)
#         return None
#
#     def db_for_write(self, model, **hints):
#         """
#         Attempts to write locker_statistic models go to locker_statistics_db.
#         """
#         if model._meta.app_label in self.route_app_labels:
#             return self.route_app_labels.get(model._meta.app_label)
#         return None
#
#     def allow_relation(self, obj1, obj2, **hints):
#         """
#         Allow relations if a model in the locker_statistic models is involved.
#         """
#         if (
#             obj1._meta.app_label in self.route_app_labels or
#             obj2._meta.app_label in self.route_app_labels
#         ):
#             return True
#         return None
#
#     def allow_migrate(self, db, app_label, model_name=None, **hints):
#         """
#         Make sure the locker_statistic app only appear in the
#         'locker_statistics' database.
#         """
#         if app_label in self.route_app_labels:
#             return db == self.route_app_labels.get(app_label)
#         return None


LOCKER_STATISTIC_DB = "locker_statistics_db"


class LockerStatisticsDBRouter:
    """
    A router to control all database operations on models in the
    locker_statistic applications.
    """
    route_app_labels = {'locker_statistic'}

    def db_for_read(self, model, **hints):
        """
        Attempts to read locker_statistic models go to locker_statistics_db.
        """
        if model._meta.app_label in self.route_app_labels:
            return LOCKER_STATISTIC_DB
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write locker_statistic models go to locker_statistics_db.
        """
        if model._meta.app_label in self.route_app_labels:
            return LOCKER_STATISTIC_DB
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the locker_statistic app is involved.
        """
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the locker_statistic app only appear in the 'locker_statistics_db' database.
        """
        if db == LOCKER_STATISTIC_DB:
            return app_label in self.route_app_labels
        if app_label in self.route_app_labels:
            return db == LOCKER_STATISTIC_DB
        return None
