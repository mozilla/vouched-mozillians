#!/bin/sh

DATABASE_URL='mysql://root:root@db:3306/mozillians' ./manage.py migrate
DATABASE_URL='mysql://root:root@db:3306/mozillians' ./manage.py dumpdata --all --indent 4 -o data.json -v 1 \
  -e sessions \
  -e cities_light \
  -e axes \
  -e thumbnail \
  -e admin.logentry

echo "data in data.json"
