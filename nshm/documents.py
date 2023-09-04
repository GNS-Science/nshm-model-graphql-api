# documents.py

from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry

from nshm import models

@registry.register_document
class SeismicHazardModelDocument(Document):

    class Index:
        name = 'seismic_hazard_models'
        # See Elasticsearch Indices API reference for available settings
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}
            
    class Django:
        model = models.SeismicHazardModel # The model associated with this Document
        fields = [
            "version",
            "notes",
        ]

@registry.register_document
class HazardSolutionDocument(Document):
    class Index:
        name = 'hazard_solutions'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}
    class Django:
        model = models.HazardSolution # The model associated with this Document
        fields = [
            "solution_id",
            "created",
            "vs30",
            "notes",
        ]