# Submission System

## Requirements

1. nodejs
2. postgresql
3. rabbitmq
4. redis
5. auth system (https://github.com/tjumyk/auth) (other oauth providers like GitLab are also possible)

## Setup

1. prepare git repo
```bash
git submodule init
git submodule update
```

2. prepare python environment
```bash
# prepare a python virtual environment first
pip install -r requirements.txt
```

3. build front-end

For node version >= 17:
```bash
cd angular
NODE_OPTIONS=--openssl-legacy-provider npm run build
cd ..
```

For node version < 17:
```bash
cd angular
npm run build
cd ..
```

4. setup database
```bash
createuser submit -P
# put a new password when prompt

createdb submit -O submit
```

## Register client in auth system

1. Access '<auth-system-url>/admin/oauth/clients/new'
2. Input details of submit app. The `Redirect URL` should be `<submit-system-url>/oauth-callback`.
3. Click 'Add' button
4. Click 'Download Client Configuration File' button to download the oauth config file, put it in project root.

## Configuration

```bash
cp config.example.json config.json
# edit config.json
```

### Edit `config.json`

1. Update `SECRET_KEY` with a good random string, e.g. using the following script to generate one:
```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(8))'
```

2. Update `SQLALCHEMY_DATABASE_URI` with a postgresql db connection url, `postgresql://submit:PASSWORD@127.0.0.1:5432/submit`. (replace `PASSWORD` with real password)
3. Delete `SYNC_WORKER`
4. Edit `SITE` and `MAIL` according to real setup
5. Delete `broker_use_ssl` in `AUTO_TEST`

## Initialization

```bash
export PYTHONPATH="$PWD:$PWD/submit-testbot"
export FLASK_APP=server.py
flask create-db
flask init-db
flask init-email-subscriptions
```

## Run

### before run

The following environment variables are required to run the following servers

```bash
export PYTHONPATH="$PWD:$PWD/submit-testbot"
export FLASK_APP=server.py
```

### Run main server

```bash
flask run -p 8888
```

### Run period-worker

```bash
python period_worker.py
```

### Run meta-bot

```bash
celery -A testbot.bot worker -Q testbot_meta -l info -n 'metabot@%h' -c 1 
```

### Run anti-plagiarism bot

First, need to start a server separately 
```bash
python anti_plagiarism/api_server.py
```

Then, start the bot process
```bash
celery -A testbot.bot worker -Q testbot_anti_plagiarism -l info -n 'apbot@%h' -c 1 
```

## Run test bot (possibly in a different server)

See [testbot project](https://github.com/tjumyk/submit-testbot)
