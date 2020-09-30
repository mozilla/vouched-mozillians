# Migrating from mysql to postgres

First make sure you have a clean local environment:

```
docker-compose down -v
rm .env
cp env-dist .env
```

Then bring just the mysql container up, so no migrations are run yet (if they are futher steps will fail):

```
docker-compose up db
```

Import the mysql dump:

```
cat path/to/dump.sql | pv | docker exec -i vouched-mozillians_db_1 /usr/bin/mysql -u mozillians --password=mozillians mozillians
```

Open a shell in your web container, run all subsequent commands in this:

```
docker-compose run web bash
```

Dump the mysql data to a json fixture:

```
bin/migrate_mysql_to_json.sh
```

You can now stop and delete the mysql container if you like.

Load from the json fixture into your postgres db:

```
bin/migrate_json_to_postgres.sh
```

You're done! Run the site with:

```
docker-compose up web
```
