FROM python:3.10

WORKDIR /app

RUN apt update -qq && apt install -y gcc default-libmysqlclient-dev

RUN groupadd -r cystack && useradd -r -g cystack -s /usr/sbin/nologin -c "CyStack user" cystack

RUN pip install --upgrade pip

COPY requirements.txt /tmp/

RUN pip install -r /tmp/requirements.txt

EXPOSE 8000

COPY . /app

RUN mkdir media

RUN chown -R cystack: media

USER cystack

ENV PROD_ENV prod

CMD gunicorn -w 3 -t 120 -b 0.0.0.0:8000 server_config.wsgi:application & daphne -b 0.0.0.0 -p 8001 server_config.asgi:application || true

#  || true & python cron_task.py || true

# & python manage.py rqworker default || true
