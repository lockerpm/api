FROM python:3.10

WORKDIR /app

RUN apt update -qq && apt install -y gcc default-libmysqlclient-dev

RUN groupadd -r cystack && useradd -r -g cystack -s /usr/sbin/nologin -c "CyStack user" cystack

RUN pip install --upgrade pip

COPY requirements.txt /tmp/

RUN pip install -r /tmp/requirements.txt

EXPOSE 8000

COPY ./src/ /app

USER cystack

ENV PROD_ENV staging

CMD gunicorn -w 5 -t 120 -b 0.0.0.0:8000 server_config.wsgi:application

# CMD python manage.py migrate; gunicorn -w 3 -t 120 -b 0.0.0.0:8000 server_config.wsgi:application || true & python cron_task.py || true 

# & python manage.py rqworker default || true