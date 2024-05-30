"""Define graphene model for nzshm_model class."""

import logging
from typing import Iterator, Optional

import graphene
import nzshm_model as nm
from graphene import relay

log = logging.getLogger(__name__)


class NshmModel(graphene.ObjectType):

    class Meta:
        interfaces = (relay.Node,)

    version = graphene.String()
    title = graphene.String()

    def resolve_id(self, info):
        """resolver for the relay.Node Interface."""
        return self.version

    @classmethod
    def get_node(cls, info, version: str):
        return get_nshm_model(version)


def get_nshm_models() -> Iterator[NshmModel]:
    for version in nm.all_model_versions():
        yield NshmModel(version=version)


def get_nshm_model(version: str) -> Optional[NshmModel]:
    model = nm.get_model_version(version)
    return NshmModel(version=model.version, title=model.title) if model else None
