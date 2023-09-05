import sys
from elasticsearch_dsl import connections
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from django_elasticsearch_dsl.management.commands.search_index import Command as DED_Command
from django_elasticsearch_dsl.registries import registry

class Command(DED_Command):
    help = 'Manage elasticsearch index custom connections.'

    def __init__(self, *args, **kwargs):
        # print(args, kwargs)
        super(BaseCommand, self).__init__(*args, **kwargs)

        print(settings.ELASTICSEARCH_DSL)
        print(connections)
        self.es_conn = connections.get_connection(settings.ELASTICSEARCH_DSL['default'])
        print(self.es_conn) # from DED
        self.stdout = sys.stdout

    def _create(self, models, aliases, options):
        for index in registry.get_indices(models):
            alias_exists = index._name in aliases
            if not alias_exists:
                self.stdout.write("Creating index '{}'".format(index._name))
                index.create(using=self.es_conn)
            elif options['action'] == 'create':
                self.stdout.write(
                    "'{}' already exists as an alias. Run '--delete' with"
                    " '--use-alias' arg to delete indices pointed at the "
                    "alias to make index name available.".format(index._name)
                )


    def _delete(self, models, aliases, options):
        index_names = [index._name for index in registry.get_indices(models)]

        if not options['force']:
            response = input(
                "Are you sure you want to delete "
                "the '{}' indices? [y/N]: ".format(", ".join(index_names)))
            if response.lower() != 'y':
                self.stdout.write('Aborted')
                return False

        if options['use_alias']:
            for index in index_names:
                alias_exists = index in aliases
                if alias_exists:
                    self._delete_alias_indices(index)
                elif self.es_conn.indices.exists(index=index):
                    self.stdout.write(
                        "'{}' refers to an index, not an alias. Run "
                        "'--delete' without '--use-alias' arg to delete "
                        "index.".format(index)
                    )
                    return False
        else:
            for index in registry.get_indices(models):
                alias_exists = index._name in aliases
                if not alias_exists:
                    self.stdout.write("Deleting index '{}'".format(index._name))
                    index.delete(ignore=404, using=self.es_conn)
                elif options['action'] == 'rebuild':
                    self._delete_alias_indices(index._name)
                elif options['action'] == 'delete':
                    self.stdout.write(
                        "'{}' refers to an alias, not an index. Run "
                        "'--delete' with '--use-alias' arg to delete indices "
                        "pointed at the alias.".format(index._name)
                    )
                    return False

        return True