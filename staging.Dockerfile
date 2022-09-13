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

CMD python manage.py migrate; gunicorn -w 3 -b 0.0.0.0:8000 server_config.wsgi:application & python cron_task.py