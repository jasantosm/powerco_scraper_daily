#!/bin/sh

./cloud_sql_proxy -instances=powerco:us-east4:xmdata=tcp:3306 -credential_file=credentials.json &
sleep 10
gunicorn --bind :$PORT --workers 1 --threads 8 main:app