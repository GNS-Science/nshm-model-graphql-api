import graphene

import nshm.schema
import pipeline.schema
from nzshm_model_graphql_api import __version__


class Query(nshm.schema.Query, pipeline.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    about = graphene.String(description="About this API ")

    def resolve_about(root, info, **args):
        return f"Hello World, I am nshm_model_graphql_api version {__version__}"

    version = graphene.String(description="API version string")

    def resolve_version(root, info, **args):
        return __version__


schema = graphene.Schema(query=Query)
