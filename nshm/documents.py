# documents.py

from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry

from nshm import models

COMMON_INDEX = 'toshi_nshm_models_index'
models_index = Index(COMMON_INDEX)
models_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)

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
        #return object_instance.pk
        return f"{cls.Django.model.__name__}_{object_instance.pk}"

@registry.register_document
class SeismicHazardModelDocument(DocumentWithNodeId):

    class Index:
        name = COMMON_INDEX
            
    class Django:
        model = models.SeismicHazardModel # The model associated with this Document
        fields = [
            "id",
            "version",
            "notes",
        ]

    source_logic_tree = fields.ObjectField(properties={
        'version': fields.TextField(),
    })
    gmcm_logic_tree = fields.ObjectField(properties={
        'version': fields.TextField(),
    })

@registry.register_document
class SourceLogicTreeDocument(DocumentWithNodeId):
    class Index:
        name = COMMON_INDEX

    class Django:
        model = models.SourceLogicTree
        fields = [
            'version',
            'notes'
        ]

    seismic_hazard_models = fields.NestedField(properties={
        'version': fields.TextField(),
        'id': fields.TextField()        
    })
    
    slt_weighted_components = fields.NestedField(properties={
        'weight': fields.TextField(),
        'id': fields.TextField()
    })    

@registry.register_document
class SourceLogicTreeComponentDocument(DocumentWithNodeId):
    class Index:
        name = COMMON_INDEX

    class Django:
        model = models.SourceLogicTreeComponent
        fields = [
            'tag', 
            'notes',
            'inversion_toshi_id',
            'background_toshi_id',
            'tectonic_region',
            'group'
        ]

    slt_weighted_components = fields.NestedField(properties={
        'weight': fields.TextField(),
        'id': fields.TextField()        
    })


@registry.register_document
class SourceLogicTreeWeightedComponentDocument(DocumentWithNodeId):
    
    class Index:
        name = COMMON_INDEX
    
    class Django:
        model = models.SourceLogicTreeWeightedComponent
        fields = [
            'weight',
        ]

    source_logic_tree = fields.ObjectField(properties={
        'version': fields.TextField(),
        'id': fields.TextField()        
    })

    source_logic_tree_component = fields.ObjectField(properties={
        'tag': fields.TextField(),
        'id': fields.TextField()        
    })


@registry.register_document
class HazardSolutionDocument(DocumentWithNodeId):
    class Index:
        name = COMMON_INDEX

    class Django:
        model = models.HazardSolution # The model associated with this Document
        fields = [
            "id",
            "solution_id",
            "created",
            "vs30",
            "notes",
        ]