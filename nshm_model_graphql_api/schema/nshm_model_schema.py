"""Define graphene model for nzshm_model class."""

import logging
from typing import Iterator, Optional

import graphene
import nzshm_model as nm
from graphene import relay

from .nshm_model_sources_schema import SourceLogicTree

log = logging.getLogger(__name__)


class NshmModel(graphene.ObjectType):
    """A custom Node representing an entire model."""

    class Meta:
        interfaces = (relay.Node,)

    version = graphene.String()
    title = graphene.String()
    source_logic_tree = graphene.Field(SourceLogicTree)

    def resolve_id(self, info):
        return self.version

    @staticmethod
    def resolve_source_logic_tree(root, info, **kwargs):
        log.info(f"resolve_source_logic_tree root: {root} kwargs: {kwargs}")
        return SourceLogicTree(
            model_version=root.version
        )  # , branch_sets=get_branch_sets(slt))

    @classmethod
    def get_node(cls, info, version: str):
        return get_nshm_model(version)


def get_nshm_models() -> Iterator[NshmModel]:
    for version in nm.all_model_versions():
        yield NshmModel(version=version)


def get_nshm_model(version: str) -> Optional[NshmModel]:
    model = nm.get_model_version(version)
    return NshmModel(version=model.version, title=model.title) if model else None
