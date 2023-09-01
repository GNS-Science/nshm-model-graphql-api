import graphene

import nshm.schema
import pipeline.schema


class Query(nshm.schema.Query, pipeline.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass


schema = graphene.Schema(query=Query)
