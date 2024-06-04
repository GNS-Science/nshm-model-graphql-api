"""The main API schema."""

import logging
from typing import Optional

import graphene
from graphene import relay

from nshm_model_graphql_api import __version__

from .nshm_model_schema import (
    NshmModel,
    get_current_model_version,
    get_nshm_model,
    get_nshm_models,
)

log = logging.getLogger(__name__)


class QueryRoot(graphene.ObjectType):
    """This is the entry point for all graphql query operations."""

    node = relay.Node.Field()
    about = graphene.String(description="About this API ")
    version = graphene.String(description="API version string")
    current_model_version = graphene.String()

    get_models = graphene.List(NshmModel)

    def resolve_get_models(root, info, **args):
        return get_nshm_models()

    get_model = graphene.Field(NshmModel, version=graphene.String(required=False))

    def resolve_get_model(root, info, version: Optional[str] = None):
        return get_nshm_model(version)  # if version else get_nshm_model()

    def resolve_current_model_version(root, info, **args):
        return get_current_model_version()

    def resolve_about(root, info, **args):
        return "Hello, I am nshm_model_graphql_api, version: %s!" % __version__

    def resolve_version(root, info, **args):
        return __version__


schema_root = graphene.Schema(query=QueryRoot, mutation=None, auto_camelcase=False)
