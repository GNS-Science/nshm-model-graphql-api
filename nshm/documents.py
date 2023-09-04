# documents.py

from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry

from nshm import models

class BaseDocumentIndex(Document):
    class Index:
        name = 'nshm_model'
        # See Elasticsearch Indices API reference for available settings
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

@registry.register_document
class SeismicHazardModelDocument(BaseDocumentIndex):
    class Django:
        model = models.SeismicHazardModel # The model associated with this Document

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            "version",
            "notes",
        ]

@registry.register_document
class HazardSolutionDocument(BaseDocumentIndex):

    class Django:
        model = models.HazardSolution # The model associated with this Document
        fields = [
            "solution_id",
            "created",
            "vs30",
            "notes",
            # "location_lists",
            # "slt_components",
        ]