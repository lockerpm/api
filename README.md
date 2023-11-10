<p align="center">
  <img src="https://s.cystack.net/resource/home/content/06122138/locker-logo.png" alt="Locker" width="50%"/>
</p>

-------------------

## What is Locker?

Locker Password Manager (also referred to as Locker) is a cross-platform password management solution: Locker can be 
used as a Web, Mobile, Browser Extension, and Desktop application.

Locker is designed to help Users and Organizations manage their confidential data, especially login credentials 
including passwords. However, to be able to access and decrypt the data in Locker, users need to memorize **ONLY** one 
item: their **Master Password**.

## The Developer - CyStack

Locker Password Manager is developed by CyStack, one of the leading cybersecurity companies in Vietnam. 
CyStack is a member of Vietnam Information Security Association (VNISA) and Vietnam Association of CyberSecurity 
Product Development. CyStack is a partner providing security solutions and services for many large domestic and 
international enterprises.

CyStack’s research has been featured at the world’s top security events such as BlackHat USA (USA), 
BlackHat Asia (Singapore), T2Fi (Finland), XCon - XFocus (China)... CyStack experts have been honored by global 
corporations such as Microsoft, Dell, Deloitte, D-link...

## Locker API

The Locker API project contains the APIs, and some services needed for the "backend" of Locker.

This project is written in Python using Django with Django Rest Framework (DRF). The database is MySQL Server.


## Developer Documentation

### Setup Guide

This section will show you how to set up a local Locker server for development purposes.

#### Clone the repository

1. Clone the Locker Server project:

```
git clone -b selfhosted https://github.com/lockerpm/api.git
```

2. Open a terminal and navigate to the root of the cloned repository


#### Config environment variables

1. Copy the example environment file

```
cp dev/.env.example .env
```

2. Open `.env` with your preferred editor.

3. Change your environment variables or use their default values. Save and quit this file.


#### Run local server

1. Use the virtual environment and active the virtual environment
```
python -m  venv <virtual-environment-name>
```

```
source venv/bin/active
```

2. Install requirements.txt

```
pip install -r requirements.txt
```

3. Run the database migrations and start local server

```
python manage.py migrate
```

```
python manage.py runserver 127.0.0.1:8000
```

Now, the local server will be run at `http://127.0.0.1:8000`


### Database

Locker Server primarily stores data in MySQL. The data access layer uses the Django ORM.

#### Update the database

You should run the `python manage.py migrate` command helper whenever you sync the new version from repository or create 
a new migration script. 

#### Modifying the database

The process for modifying the data is described in `locker_server/api_orm/migrations` folders.


### Environment variables

1. Databases

- MYSQL_USERNAME: Your Database username
- MYSQL_PASSWORD: Your Database password
- MYSQL_DATABASE: The database name
- MYSQL_HOST: The database host
- MYSQL_PORT: The MySQL port

Example
```
MYSQL_USERNAME=root
MYSQL_PASSWORD=rootmysqlpassword
MYSQL_DATABASE=locker
MYSQL_HOST=localhost
MYSQL_PORT=3306
```

2. Caching

The Locker Server use Redis as caching database

- CACHE_LOCATION: The redis location

Example
```
CACHE_LOCATION=redis://:@127.0.0.1:6379/1
```

3. WebSocket channels

- CHANNEL_REDIS_LOCATION: The redis location to run websocket channel

Example
```
CHANNEL_REDIS_LOCATION=redis://:@127.0.0.1:6379/1?ssl_cert_reqs=none
```


## Whitepaper

[Locker Whitepaper](https://locker.io/whitepaper)

## Deploy

<p align="center">
  <a href="https://hub.docker.com/u/bitwarden/" target="_blank">
    <img src="https://i.imgur.com/SZc8JnH.png" alt="docker" />
  </a>
</p>

You can deploy Locker API using Docker containers on Windows, macOS and Linux distributions.


### Requirements

- [Docker](https://www.docker.com/community-edition#/download)

## Contribute

Code contributions are welcome! You can commit any pull requests against the `main` branch. 
Learn more about how to contribute by reading the [Contributing Guidelines](). 
Check out the [Contributing Documentation]() for how to get started with your first contribution.

We also run a bugbounty program on [WhiteHub](https://whitehub.net/programs/locker). You can submit reports on WhiteHub.
We will review the report and discuss with you.


## License

[GPLv3](./LICENSE)