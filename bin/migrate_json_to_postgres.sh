#!/bin/sh

./manage.py migrate
./manage.py sqlflush | ./manage.py dbshell
./manage.py loaddata -v 3 /code/data.json
rm /code/data.json
