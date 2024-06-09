"""Define graphene model for nzshm_model gmm logic tree classes."""

import json
import logging
from functools import lru_cache

import graphene
from graphene import relay

from .nshm_model_sources_schema import get_model_by_version

log = logging.getLogger(__name__)


# TODO: this method belongs on the nzshm-model gmcm class
@lru_cache
def get_branch_set(model_version, short_name):
    glt = get_model_by_version(model_version).gmm_logic_tree
    log.debug(f"glt {glt}")
    for bs in glt.branch_sets:
        if bs.short_name == short_name:
            return bs
    assert 0, f"branch set {short_name} was not found"  # pragma: no cover


# TODO: this method belongs on the nzshm-model gmcm class
@lru_cache
def get_logic_tree_branch(model_version, branch_set_short_name, gsim_name, gsim_args):
    log.info(
        f"get_logic_tree_branch: {branch_set_short_name} gsim_name: {gsim_name} gsim_args: {gsim_args}"
    )
    branch_set = get_branch_set(model_version, branch_set_short_name)
    for ltb in branch_set.branches:
        if (ltb.gsim_name == gsim_name) and (ltb.gsim_args == json.loads(gsim_args)):
            return ltb
    assert (
        0
    ), f"branch with gsim_name: {gsim_name} gsim_args: {gsim_args} was not found"  # pragma: no cover


class GmmLogicTreeBranch(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    model_version = graphene.String()
    branch_set_short_name = graphene.String()
    gsim_name = graphene.String()
    gsim_args = graphene.JSONString()
    tectonic_region_type = graphene.String()  # should be an enum
    weight = graphene.Float()

    def resolve_id(self, info):
        return f"{self.model_version}|{self.branch_set_short_name}|{self.gsim_name}|{json.dumps(self.gsim_args)}"

    @classmethod
    def get_node(cls, info, node_id: str):
        model_version, branch_set_short_name, gsim_name, gsim_args = node_id.split("|")
        gltb = get_logic_tree_branch(
            model_version, branch_set_short_name, gsim_name, gsim_args
        )
        return GmmLogicTreeBranch(
            model_version=model_version,
            branch_set_short_name=branch_set_short_name,
            tectonic_region_type=gltb.tectonic_region_type,
            gsim_name=gltb.gsim_name,
            gsim_args=gltb.gsim_args,
            weight=gltb.weight,
        )


class GmmBranchSet(graphene.ObjectType):
    """Ground Motion Model branch sets,

    to ensure that the wieghts of the enclosed branches sum to 1.0
    """

    class Meta:
        interfaces = (relay.Node,)

    model_version = graphene.String()
    short_name = graphene.String()
    long_name = graphene.String()
    tectonic_region_type = graphene.String()
    branches = graphene.List(GmmLogicTreeBranch)

    def resolve_id(self, info):
        return f"{self.model_version}:{self.short_name}"

    @classmethod
    def get_node(cls, info, node_id: str):
        model_version, short_name = node_id.split(":")
        bs = get_branch_set(model_version, short_name)
        return GmmBranchSet(
            model_version=model_version,
            tectonic_region_type=bs.tectonic_region_type,
            short_name=bs.short_name,
            long_name=bs.long_name,
        )

    @staticmethod
    def resolve_branches(root, info, **kwargs):
        log.info(f"resolve_branches root: {root} kwargs: {kwargs}")
        bs = get_branch_set(root.model_version, root.short_name)
        for ltb in bs.branches:
            log.debug(ltb)
            yield GmmLogicTreeBranch(
                model_version=root.model_version,
                branch_set_short_name=root.short_name,
                tectonic_region_type=ltb.tectonic_region_type,
                weight=ltb.weight,
                gsim_name=ltb.gsim_name,
                gsim_args=ltb.gsim_args,
            )


class GroundMotionModelLogicTree(graphene.ObjectType):
    """A custom Node representing the GMM logic tree of a given model."""

    class Meta:
        interfaces = (relay.Node,)

    model_version = graphene.String()
    branch_sets = graphene.List(GmmBranchSet)

    def resolve_id(self, info):
        return self.model_version

    @classmethod
    def get_node(cls, info, model_version: str):
        return GroundMotionModelLogicTree(model_version=model_version)

    @staticmethod
    def resolve_branch_sets(root, info, **kwargs):
        log.info(f"resolve_branch_sets root: {root} kwargs: {kwargs}")
        glt = get_model_by_version(root.model_version).gmm_logic_tree
        for bs in glt.branch_sets:
            yield GmmBranchSet(
                model_version=root.model_version,
                short_name=bs.short_name,
                long_name=bs.long_name,
                tectonic_region_type=bs.tectonic_region_type,
            )