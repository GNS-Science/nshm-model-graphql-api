"""Define graphene model for nzshm_model class."""

import logging
from typing import Iterator, Optional

import graphene
import nzshm_model as nm
from graphene import relay

log = logging.getLogger(__name__)


class SourceLogicTreeBranch(graphene.ObjectType):
    model_version = graphene.String()
    weight = graphene.Float()
    tag = graphene.String()


class SourceBranchSet(graphene.ObjectType):
    model_version = graphene.String()
    short_name = graphene.String()
    long_name = graphene.String()
    branches = graphene.List(SourceLogicTreeBranch)

    def resolve_branches(root, info, **kwargs):
        log.info(f"resolve_branches root: {root} kwargs: {kwargs}")
        slt = nm.get_model_version(root.model_version).source_logic_tree
        for bs in slt.branch_sets:
            if bs.short_name == root.short_name:
                for ltb in bs.branches:
                    yield SourceLogicTreeBranch(root.model_version, ltb.weight, ltb.tag)


class SourceLogicTree(graphene.ObjectType):
    model_version = graphene.String()
    branch_sets = graphene.List(SourceBranchSet)

    @staticmethod
    def resolve_branch_sets(root, info, **kwargs):
        log.info(f"resolve_branch_sets root: {root} kwargs: {kwargs}")
        slt = nm.get_model_version(root.model_version).source_logic_tree
        for bs in slt.branch_sets:
            yield SourceBranchSet(root.model_version, bs.short_name, bs.long_name)


class NshmModel(graphene.ObjectType):
    """graphene custom Node representind an entire model."""

    class Meta:
        interfaces = (relay.Node,)

    version = graphene.String()
    title = graphene.String()
    source_logic_tree = graphene.Field(SourceLogicTree)

    def resolve_id(self, info):
        """resolver for the relay.Node Interface."""
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
