import graphene
from graphene import relay

import nshm.schema
import pipeline.schema
from nzshm_model_graphql_api import __version__

from nshm.schema import SeismicHazardModel #, HazardSolution
from nzshm_model_graphql_api import settings

class Query(nshm.schema.Query, pipeline.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project

    node = relay.Node.Field()
    about = graphene.String(description="About this API ")
    version = graphene.String(description="API version string")

    def resolve_version(root, info, **args):
        return __version__

    def resolve_about(root, info, **args):
        return f"Hello World, I am nshm_model_graphql_api version {__version__}"

schema = graphene.Schema(query=Query)
