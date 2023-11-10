import contextvars

context_var = contextvars.ContextVar("DB", default='default')


def set_current_db_name(db):
    context_var.set(db)


def get_current_db_name():
    return context_var.get()
