"""Define graphene model for nzshm_model source logic tree classes."""

import logging

import graphene
import nzshm_model as nm
from graphene import relay

log = logging.getLogger(__name__)


# TODO: this method belongs on the nzshm-model slt class
def get_branch_set(slt, short_name):
    for bs in slt.branch_sets:
        if bs.short_name == short_name:
            return bs
    assert 0, f"branch set {short_name} was not found"  # pragma: no cover


# TODO: this method belongs on the nzshm-model slt class
def get_logic_tree_branch(slt, short_name, tag):
    log.info(f"rget_logic_tree_branch: {short_name} tag: {tag}")
    branch_set = get_branch_set(slt, short_name)
    for ltb in branch_set.branches:
        if ltb.tag == tag:
            return ltb
        print(short_name, ltb.tag)
    assert 0, f"branch with {tag} was not found"  # pragma: no cover


class SourceLogicTreeBranch(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    model_version = graphene.String()
    branch_set_short_name = graphene.String()
    tag = graphene.String()
    weight = graphene.Float()

    def resolve_id(self, info):
        return f"{self.model_version}:{self.branch_set_short_name}:{self.tag}"

    @staticmethod
    def resolve_weight(root, info, **kwargs):
        log.info(f"resolve SourceLogicTreeBranch.weight root: {root} kwargs: {kwargs}")
        if root.weight:
            return root.weight
        slt = nm.get_model_version(root.model_version).source_logic_tree
        ltb = get_logic_tree_branch(slt, root.branch_set_short_name, root.tag)
        return ltb.weight

    @classmethod
    def get_node(cls, info, node_id: str):
        model_version, branch_set_short_name, tag = node_id.split(":")
        return SourceLogicTreeBranch(
            model_version=model_version,
            branch_set_short_name=branch_set_short_name,
            tag=tag,
        )


class SourceBranchSet(graphene.ObjectType):

    class Meta:
        interfaces = (relay.Node,)

    model_version = graphene.String()
    short_name = graphene.String()
    long_name = graphene.String()
    branches = graphene.List(SourceLogicTreeBranch)

    def resolve_id(self, info):
        return f"{self.model_version}:{self.short_name}"

    @classmethod
    def get_node(cls, info, node_id: str):
        model_version, short_name = node_id.split(":")
        return SourceBranchSet(model_version=model_version, short_name=short_name)

    @staticmethod
    def resolve_long_name(root, info, **kwargs):
        if root.long_name:
            return root.long_name
        slt = nm.get_model_version(root.model_version).source_logic_tree
        bs = get_branch_set(slt, root.short_name)
        return bs.long_name

    @staticmethod
    def resolve_branches(root, info, **kwargs):
        log.info(f"resolve_branches root: {root} kwargs: {kwargs}")
        slt = nm.get_model_version(root.model_version).source_logic_tree
        bs = get_branch_set(slt, root.short_name)
        for ltb in bs.branches:
            sltb = SourceLogicTreeBranch(
                model_version=root.model_version,
                branch_set_short_name=bs.short_name,
                weight=ltb.weight,
                tag=ltb.tag,
            )
            # log.debug(f'sltb {sltb}')
            yield sltb


class SourceLogicTree(graphene.ObjectType):
    """A custom Node representing the source logic tree of a given model."""

    class Meta:
        interfaces = (relay.Node,)

    model_version = graphene.String()
    branch_sets = graphene.List(SourceBranchSet)

    def resolve_id(self, info):
        return self.model_version

    @classmethod
    def get_node(cls, info, model_version: str):
        return SourceLogicTree(model_version=model_version)

    @staticmethod
    def resolve_branch_sets(root, info, **kwargs):
        log.info(f"resolve_branch_sets root: {root} kwargs: {kwargs}")
        slt = nm.get_model_version(root.model_version).source_logic_tree
        for bs in slt.branch_sets:
            yield SourceBranchSet(
                model_version=root.model_version,
                short_name=bs.short_name,
                long_name=bs.long_name,
            )
