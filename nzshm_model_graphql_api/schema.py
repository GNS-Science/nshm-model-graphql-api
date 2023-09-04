import graphene
from graphene import relay

import nshm.schema
import pipeline.schema
from nzshm_model_graphql_api import __version__

from nshm.schema import SeismicHazardModel #, HazardSolution
from elasticsearch import Elasticsearch
import elasticsearch_dsl


class SearchResult(graphene.Union):
    class Meta:
        types = (SeismicHazardModel, )

class SearchResultConnection(relay.Connection):
    class Meta:
        node = SearchResult
    total_count = graphene.Field(graphene.Int)

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return len(root.edges)

class Search(graphene.ObjectType):
    ok = graphene.Boolean()
    search_result = relay.ConnectionField(SearchResultConnection)

class Query(nshm.schema.Query, pipeline.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    about = graphene.String(description="About this API ")
    search = graphene.Field(Search, search_term=graphene.String())
    version = graphene.String(description="API version string")

    def resolve_version(root, info, **args):
        return __version__

    def resolve_about(root, info, **args):
        return f"Hello World, I am nshm_model_graphql_api version {__version__}"

    def resolve_search(root, info, **kwargs):
        # t0 = dt.utcnow()

        search_term = kwargs.get('search_term')
        print(search_term)
        client = Elasticsearch()
        s = elasticsearch_dsl.Search().using(client)
        q = elasticsearch_dsl.Q("multi_match", query=search_term)
        search_result = list(s.query(q))
        for sr in search_result:
            print(sr, sr.notes)
            print(sr.meta, sr.meta.doc_type, sr.meta.id)            
            print(dir(sr))

        # db_metrics.put_duration(__name__, 'resolve_search' , dt.utcnow()-t0)
        return Search(ok=True, search_result=[])

schema = graphene.Schema(query=Query)
