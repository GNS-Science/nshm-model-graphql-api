ref: https://docs.graphene-python.org/projects/django/en/latest/tutorial-relay/


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