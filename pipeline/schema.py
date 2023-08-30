from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from pipeline import models

# Graphene will automatically map the Category model's fields onto the CategoryNode.
# This is configured in the CategoryNode's Meta class (as you can see below)
class OpenquakeHazardTask(DjangoObjectType):
    class Meta:
        model = models.OpenquakeHazardTask
        filter_fields = ['general_task_id', 'part_of__version']
        interfaces = (relay.Node, )

class Query(ObjectType):
    openquake_hazard_task = relay.Node.Field(OpenquakeHazardTask)
    all_openquake_hazard_tasks = DjangoFilterConnectionField(OpenquakeHazardTask)
