"""Define graphene model for nzshm_model source logic tree classes."""

import logging

import graphene
import nzshm_model as nm
from graphene import relay
from graphql import GraphQLError
from graphql_relay import from_global_id, to_global_id
from nzshm_model.logic_tree.source_logic_tree.version2 import logic_tree

log = logging.getLogger(__name__)


# TODO: this method belongs on the nzshm-model slt class
def get_branch_set(slt, short_name):
    for bs in slt.branch_sets:
        if bs.short_name == short_name:
            return bs
    assert 0, f"branch set {short_name} was not found"  # pragma: no cover


# TODO: this method belongs on the nzshm-model slt class
def get_logic_tree_branch(slt, short_name, tag):
    log.info(f"get_logic_tree_branch: {short_name} tag: {tag}")
    branch_set = get_branch_set(slt, short_name)
    for ltb in branch_set.branches:
        if ltb.tag == tag:
            return ltb
        # print(short_name, ltb.tag)
    assert 0, f"branch with {tag} was not found"  # pragma: no cover


def get_logic_tree_branch_source(slt, short_name, nrml_id):
    log.info(f"get_logic_tree_branch_source: {short_name} nrml_id: {nrml_id}")
    branch_set = get_branch_set(slt, short_name)
    for ltb in branch_set.branches:
        for src in ltb.sources:
            if src.nrml_id == nrml_id:
                return src
        print(short_name, src.nrml_id)


"""
[InversionSource(nrml_id='SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEyMDg5Mg==', rupture_rate_scaling=None,
    inversion_id='U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNjc2', rupture_set_id='RmlsZToxMDAwODc=',
    inversion_solution_type='', type='inversion'),
 DistributedSource(nrml_id='RmlsZToxMzA3Mjg=', rupture_rate_scaling=None, type='distributed')]
"""


class BranchInversionSource(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    model_version = graphene.String()
    branch_set_short_name = graphene.String()
    nrml_id = graphene.ID()
    rupture_set_id = graphene.ID()

    def resolve_id(self, info):
        klass, nrml_id = from_global_id(self.nrml_id)
        return f"{self.model_version}:{self.branch_set_short_name}:{nrml_id}"

    @classmethod
    def get_node(cls, info, node_id: str):
        log.info(f"BranchInversionSource.get_node() node_id: {node_id}")
        model_version, branch_set_short_name, nrml = node_id.split(":")
        slt = nm.get_model_version(model_version).source_logic_tree
        src = get_logic_tree_branch_source(
            slt, branch_set_short_name, to_global_id("InversionSolutionNrml", nrml)
        )
        if not src:
            raise GraphQLError(f"branch source for `{node_id}` was not found")
        return BranchInversionSource(
            model_version=model_version,
            branch_set_short_name=branch_set_short_name,
            nrml_id=src.nrml_id,
            rupture_set_id=src.rupture_set_id,
        )

    # def resolve_rupture_set_id(root, info, **kwargs):
    #     log.info(
    #         f"resolve BranchInversionSource.rupture_set_id root: {root} kwargs: {kwargs}"
    #     )
    #     if root.rupture_set_id:
    #         return root.rupture_set_id
    #     slt = nm.get_model_version(root.model_version).source_logic_tree
    #     src = get_logic_tree_branch_source(
    #         slt, root.branch_set_short_name, root.nrml_id
    #     )
    #     return src.rupture_set_id


class BranchDistributedSource(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    model_version = graphene.String()
    branch_set_short_name = graphene.String()
    tag = graphene.String()
    nrml_id = graphene.ID()


class BranchSource(graphene.Union):
    class Meta:
        types = (BranchInversionSource, BranchDistributedSource)


class SourceLogicTreeBranch(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    model_version = graphene.String()
    branch_set_short_name = graphene.String()
    tag = graphene.String()
    weight = graphene.Float()
    sources = graphene.List(BranchSource)

    def resolve_id(self, info):
        return f"{self.model_version}:{self.branch_set_short_name}:{self.tag}"

    @staticmethod
    def resolve_weight(root, info, **kwargs):
        log.info(f"resolve SourceLogicTreeBranch.weight root: {root} kwargs: {kwargs}")
        if root.weight:
            return root.weight
        slt = nm.get_model_version(root.model_version).source_logic_tree
        ltb = get_logic_tree_branch(slt, root.branch_set_short_name, root.tag)
        print(ltb.sources)
        return ltb.weight

    @staticmethod
    def resolve_sources(root, info, **kwargs):
        log.info(f"resolve SourceLogicTreeBranch.sources root: {root} kwargs: {kwargs}")
        if root.sources:
            return root.sources
        slt = nm.get_model_version(root.model_version).source_logic_tree
        ltb = get_logic_tree_branch(slt, root.branch_set_short_name, root.tag)
        for src in ltb.sources:
            if isinstance(src, logic_tree.InversionSource):
                print(src)
                yield BranchInversionSource(
                    model_version=root.model_version,
                    branch_set_short_name=root.branch_set_short_name,
                    nrml_id=src.nrml_id,
                    rupture_set_id=src.rupture_set_id,
                )

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
