ref: https://docs.graphene-python.org/projects/django/en/latest/tutorial-relay/
1

## the Sqlite3 on lambda issue

This project is a good candidate for using a sqlite3 database, especially in the exploratory, POC stages. 

But we had to solve some compatablity issues to get this working on AWS lambda . [See this guide](./SQLITE_CUSTOM_LAMBDA_BUILD.md) for more info.

## Some Useful commands

### build an ERM model
requires graphviz libraries installed `sudo apt install graphviz`

```
poetry run python manage.py graph_models -o nshm_model.png nshm pipeline
```

### Load data using djanog-extension helpers

```
# build the script
 poetry run python manage.py dumpscript nshm.OpenquakeHazardTask >scripts/nshm_openquake_hazard_task.py
# edit then run script ...
 poetry run python manage.py runscript scripts.nshm_openquake_hazard_task
```

### Dump/Load data to json

```
poetry run python manage.py dumpdata nshm.OpenquakeHazardTask -o pipeline/fixtures/oht.json --indent=2
poetry run python manage.py loaddata pipeline/fixtures/oht.json
```

### update static files

These are just the static components for admin and graphiql

```
poetry run python manage.py collectstatic -c
```

### run server options

```
poetry run python manage.py runserver
poetry run python manage.py runserver_plus
```

```
poetry shell
npx sls wsgi serve
```

### AWS OpenSearch integration

Alert we use git@github.com:daily-science/django-elasticsearch-dsl.git fork for now. This should be PR'd onto the main project.

This project now has ES settings and uses the above to maintain indexes as the django SQL db is maintained. 

You can also maintain the indexes via new manage.py commaneds e.g:

```
DEBUG=1 poetry run python manage.py search_index --create
DEBUG=1 poetry run python manage.py search_index --populate
DEBUG=1 poetry run python manage.py search_index --rebuild
DEBug=1 poetry run python manage.py search_index --help
```
