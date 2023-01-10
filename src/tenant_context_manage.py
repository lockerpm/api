#!/usr/bin/env python
import os
import sys
import dotenv


from shared.middlewares.tenant_db_middleware import set_current_db_name


def main():
    valid_env = ['prod', 'env', 'staging']
    env = os.getenv("PROD_ENV")
    if env not in valid_env:
        env = 'dev'
    if env == 'dev':
        dotenv.read_dotenv()

    setting = "server_config.settings.%s" % env
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", setting)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Set database name for the db cursor connection
    from django.db import connection
    args = sys.argv
    db = args[1]
    with connection.cursor() as cursor:
        set_current_db_name(db)
        del args[1]
        # Run the command with tenant db context
        execute_from_command_line(args)


if __name__ == '__main__':
    main()
