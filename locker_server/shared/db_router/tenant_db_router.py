from shared.middlewares.tenant_db_middleware import get_current_db_name


class TenantDBRouter:
    """
    A router to control all database operations on Tenant
    """

    def db_for_read(self, model, **hints):
        db_name = get_current_db_name()
        print("TenantDBRouter::db_for_read:", db_name)
        return db_name

    def db_for_write(self, model, **hints):
        db_name = get_current_db_name()
        print("TenantDBRouter::db_for_write:", db_name)
        return db_name

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return None
