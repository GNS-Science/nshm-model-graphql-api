from graphene import ObjectType, relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from nshm import models


# Graphene will automatically map the Category model's fields onto the CategoryNode.
# This is configured in the CategoryNode's Meta class (as you can see below)
class SourceLogicTree(DjangoObjectType):
    class Meta:
        model = models.SourceLogicTree
        filter_fields = ["version", "notes"]
        interfaces = (relay.Node,)


class SeismicHazardModel(DjangoObjectType):
    class Meta:
        model = models.SeismicHazardModel

        # Allow for some more advanced filtering here
        filter_fields = {
            "version": ["exact", "icontains", "istartswith"],
            "notes": ["icontains"],
            "source_logic_tree__version": ["exact"],
            # 'category__name': ['exact'],
        }
        interfaces = (relay.Node,)


class SourceLogicTreeSource(DjangoObjectType):
    class Meta:
        model = models.SourceLogicTreeSource
        interfaces = (relay.Node,)
        filter_fields = [
            "tag",
            "notes",
            "inversion_toshi_id",
            "group",
            "tectonic_region",
        ]


class SourceLogicTreeBranch(DjangoObjectType):
    class Meta:
        model = models.SourceLogicTreeBranch
        interfaces = (relay.Node,)


class GMCM_LogicTree(DjangoObjectType):
    """Ground Motion Characteristic Model (GMCM) Logic Tree

    A list of GMMs by tectonic region, with weights. Tectonic region weights must sum to 1.
    """

    class Meta:
        model = models.GMCMLogicTree
        filter_fields = ["version", "notes"]
        interfaces = (relay.Node,)


class Query(ObjectType):
    seismic_hazard_model = relay.Node.Field(SeismicHazardModel)
    all_seismic_hazard_models = DjangoFilterConnectionField(SeismicHazardModel)

    source_logic_tree = relay.Node.Field(SourceLogicTree)
    all_source_logic_trees = DjangoFilterConnectionField(SourceLogicTree)

    source_logic_tree_component = relay.Node.Field(SourceLogicTreeSource)
    all_source_logic_tree_components = DjangoFilterConnectionField(
        SourceLogicTreeSource
    )

    gmcm_logic_tree = relay.Node.Field(GMCM_LogicTree)
    all_gmcm_logic_trees = DjangoFilterConnectionField(GMCM_LogicTree)

    # source_logic_tree_weighted_component = relay.Node.Field(SourceLogicTreeBranch)
