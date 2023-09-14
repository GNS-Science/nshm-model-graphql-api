# documents.py

from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry

from nshm import models

class DocumentWithNodeId(Document):
    """
    Override the object ID used in the search engine to be similar to that use in Toshi_ID
    """
    @classmethod
    def generate_id(cls, object_instance):
        """
        The default behavior is to use the Django object's pk (id) as the
        elasticseach index id (_id). If needed, this method can be overloaded
        to change this default behavior.
        """
        return f"{cls.Django.model.__name__}_{object_instance.pk}"

@registry.register_document
class SeismicHazardModelDocument(DocumentWithNodeId):

    class Index:
        name = 'toshi_nshm_seismic_hazard_models' # PREFIX is important
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
class HazardSolutionDocument(DocumentWithNodeId):
    class Index:
        name = 'toshi_nshm_hazard_solutions'
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