"""Strawberry GraphQL schema.

Resolvers project the nzshm-model dataclasses (via `data.py`) into GraphQL types.
Kept at strict SDL parity with `schema.legacy.graphql` (the original Graphene
contract); enforced by `tests/test_schema_parity.py`.

Design choices (see docs/MIGRATION_LOG.md):
- `auto_camel_case=False` — snake_case field names (the established client contract).
- All scalar/list fields are nullable, matching the original Graphene defaults.
- A **custom** `Node` interface (not `strawberry.relay`) so `id` stays `ID!` and
  global-ids keep the exact `graphql_relay` base64 encoding clients/tests rely on —
  Strawberry's relay would introduce a `GlobalID` scalar and diverge.
"""

import json
import typing
from typing import Annotated

import strawberry
from graphql_relay import from_global_id, to_global_id
from strawberry.schema.config import StrawberryConfig

from nshm_model_graphql_api import __version__, data

# ---------------------------------------------------------------------------
# Scalars
# ---------------------------------------------------------------------------

JSONString = strawberry.scalar(
    typing.NewType("JSONString", object),
    serialize=lambda value: json.dumps(value),
    parse_value=lambda value: json.loads(value),
    description=(
        "Allows use of a JSON String for input / output from the GraphQL schema.\n"
        "\n"
        "Use of this type is *not recommended* as you lose the benefits of having a defined, static\n"
        "schema (one of the key benefits of GraphQL)."
    ),
)

_ID_DESCRIPTION = "The ID of the object"


# ---------------------------------------------------------------------------
# Node interface (custom — preserves `id: ID!` and graphql_relay encoding)
# ---------------------------------------------------------------------------


@strawberry.interface(description="An object with an ID")
class Node:
    @strawberry.field(description=_ID_DESCRIPTION)
    def id(self) -> strawberry.ID:  # noqa: A003  (matches legacy field name)
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Source logic tree types
# ---------------------------------------------------------------------------


@strawberry.type
class BranchInversionSource:
    nrml_id: strawberry.ID | None = None
    rupture_set_id: strawberry.ID | None = None
    inversion_id: strawberry.ID | None = None


@strawberry.type
class BranchDistributedSource:
    nrml_id: strawberry.ID | None = None


BranchSource = Annotated[
    BranchInversionSource | BranchDistributedSource,
    strawberry.union("BranchSource"),
]


@strawberry.type
class SourceLogicTreeBranch(Node):
    model_version: str | None = None
    branch_set_short_name: str | None = None
    tag: str | None = None
    weight: float | None = None

    @strawberry.field(description=_ID_DESCRIPTION)
    def id(self) -> strawberry.ID:  # noqa: A003
        return strawberry.ID(
            to_global_id("SourceLogicTreeBranch", f"{self.model_version}:{self.branch_set_short_name}:{self.tag}")
        )

    @strawberry.field
    def sources(self) -> list[BranchSource | None] | None:
        ltb = data.get_source_branch(self.model_version, self.branch_set_short_name, self.tag)
        out: list[BranchSource | None] = []
        for src in ltb.sources:
            if isinstance(src, data.InversionSource):
                out.append(
                    BranchInversionSource(
                        nrml_id=src.nrml_id,
                        rupture_set_id=src.rupture_set_id,
                        inversion_id=src.inversion_id,
                    )
                )
            elif isinstance(src, data.DistributedSource):
                out.append(BranchDistributedSource(nrml_id=src.nrml_id))
            else:
                raise RuntimeError(f"got unknown source type :{src}")  # pragma: no cover
        return out


@strawberry.type
class SourceBranchSet(Node):
    model_version: str | None = None
    short_name: str | None = None
    long_name: str | None = None

    @strawberry.field(description=_ID_DESCRIPTION)
    def id(self) -> strawberry.ID:  # noqa: A003
        return strawberry.ID(to_global_id("SourceBranchSet", f"{self.model_version}:{self.short_name}"))

    @strawberry.field
    def branches(self) -> list[SourceLogicTreeBranch | None] | None:
        bs = data.get_source_branch_set(self.model_version, self.short_name)
        return [
            SourceLogicTreeBranch(
                model_version=self.model_version,
                branch_set_short_name=bs.short_name,
                weight=ltb.weight,
                tag=ltb.tag,
            )
            for ltb in bs.branches
        ]


@strawberry.type(description="A custom Node representing the source logic tree of a given model.")
class SourceLogicTree(Node):
    model_version: str | None = None

    @strawberry.field(description=_ID_DESCRIPTION)
    def id(self) -> strawberry.ID:  # noqa: A003
        return strawberry.ID(to_global_id("SourceLogicTree", f"{self.model_version}"))

    @strawberry.field
    def branch_sets(self) -> list[SourceBranchSet | None] | None:
        slt = data.get_model_by_version(self.model_version).source_logic_tree
        return [
            SourceBranchSet(model_version=self.model_version, short_name=bs.short_name, long_name=bs.long_name)
            for bs in slt.branch_sets
        ]


# ---------------------------------------------------------------------------
# GMM logic tree types
# ---------------------------------------------------------------------------


@strawberry.type
class GmmLogicTreeBranch(Node):
    model_version: str | None = None
    branch_set_short_name: str | None = None
    gsim_name: str | None = None
    gsim_args: JSONString | None = None  # type: ignore[valid-type]  # strawberry scalar, not a static type
    tectonic_region_type: str | None = None
    weight: float | None = None

    @strawberry.field(description=_ID_DESCRIPTION)
    def id(self) -> strawberry.ID:  # noqa: A003
        return strawberry.ID(
            to_global_id(
                "GmmLogicTreeBranch",
                f"{self.model_version}|{self.branch_set_short_name}|{self.gsim_name}|{json.dumps(self.gsim_args)}",
            )
        )


@strawberry.type(
    description="Ground Motion Model branch sets,\n\nto ensure that the wieghts of the enclosed branches sum to 1.0"
)
class GmmBranchSet(Node):
    model_version: str | None = None
    short_name: str | None = None
    long_name: str | None = None
    tectonic_region_type: str | None = None

    @strawberry.field(description=_ID_DESCRIPTION)
    def id(self) -> strawberry.ID:  # noqa: A003
        return strawberry.ID(to_global_id("GmmBranchSet", f"{self.model_version}:{self.short_name}"))

    @strawberry.field
    def branches(self) -> list[GmmLogicTreeBranch | None] | None:
        bs = data.get_gmm_branch_set(self.model_version, self.short_name)
        return [
            GmmLogicTreeBranch(
                model_version=self.model_version,
                branch_set_short_name=self.short_name,
                tectonic_region_type=ltb.tectonic_region_type,
                weight=ltb.weight,
                gsim_name=ltb.gsim_name,
                gsim_args=ltb.gsim_args,
            )
            for ltb in bs.branches
        ]


@strawberry.type(description="A custom Node representing the GMM logic tree of a given model.")
class GroundMotionModelLogicTree(Node):
    model_version: str | None = None

    @strawberry.field(description=_ID_DESCRIPTION)
    def id(self) -> strawberry.ID:  # noqa: A003
        return strawberry.ID(to_global_id("GroundMotionModelLogicTree", f"{self.model_version}"))

    @strawberry.field
    def branch_sets(self) -> list[GmmBranchSet | None] | None:
        glt = data.get_model_by_version(self.model_version).gmm_logic_tree
        return [
            GmmBranchSet(
                model_version=self.model_version,
                short_name=bs.short_name,
                long_name=bs.long_name,
                tectonic_region_type=bs.tectonic_region_type,
            )
            for bs in glt.branch_sets
        ]


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


@strawberry.type(description="A custom Node representing an entire model.")
class NshmModel(Node):
    version: str | None = None
    title: str | None = None

    @strawberry.field(description=_ID_DESCRIPTION)
    def id(self) -> strawberry.ID:  # noqa: A003
        return strawberry.ID(to_global_id("NshmModel", f"{self.version}"))

    @strawberry.field
    def source_logic_tree(self) -> SourceLogicTree | None:
        return SourceLogicTree(model_version=self.version)

    @strawberry.field
    def gmm_logic_tree(self) -> GroundMotionModelLogicTree | None:
        return GroundMotionModelLogicTree(model_version=self.version)


def _build_nshm_model(model) -> NshmModel | None:
    return NshmModel(version=model.version, title=model.title) if model else None


# ---------------------------------------------------------------------------
# Node global-id dispatch (mirrors the legacy per-type get_node classmethods)
# ---------------------------------------------------------------------------


def _node_nshm_model(internal: str) -> Node | None:
    return _build_nshm_model(data.get_model(internal))


def _node_source_logic_tree(internal: str) -> Node | None:
    return SourceLogicTree(model_version=internal)


def _node_source_branch_set(internal: str) -> Node | None:
    model_version, short_name = internal.split(":")
    bs = data.get_source_branch_set(model_version, short_name)
    return SourceBranchSet(model_version=model_version, short_name=short_name, long_name=bs.long_name)


def _node_source_branch(internal: str) -> Node | None:
    model_version, branch_set_short_name, tag = internal.split(":")
    sltb = data.get_source_branch(model_version, branch_set_short_name, tag)
    return SourceLogicTreeBranch(
        model_version=model_version,
        branch_set_short_name=branch_set_short_name,
        tag=tag,
        weight=sltb.weight,
    )


def _node_gmm_logic_tree(internal: str) -> Node | None:
    return GroundMotionModelLogicTree(model_version=internal)


def _node_gmm_branch_set(internal: str) -> Node | None:
    model_version, short_name = internal.split(":")
    bs = data.get_gmm_branch_set(model_version, short_name)
    return GmmBranchSet(
        model_version=model_version,
        tectonic_region_type=bs.tectonic_region_type,
        short_name=short_name,
        long_name=bs.long_name,
    )


def _node_gmm_branch(internal: str) -> Node | None:
    model_version, branch_set_short_name, gsim_name, gsim_args = internal.split("|")
    gltb = data.get_gmm_branch(model_version, branch_set_short_name, gsim_name, gsim_args)
    return GmmLogicTreeBranch(
        model_version=model_version,
        branch_set_short_name=branch_set_short_name,
        tectonic_region_type=gltb.tectonic_region_type,
        gsim_name=gltb.gsim_name,
        gsim_args=gltb.gsim_args,
        weight=gltb.weight,
    )


_NODE_DISPATCH = {
    "NshmModel": _node_nshm_model,
    "SourceLogicTree": _node_source_logic_tree,
    "SourceBranchSet": _node_source_branch_set,
    "SourceLogicTreeBranch": _node_source_branch,
    "GroundMotionModelLogicTree": _node_gmm_logic_tree,
    "GmmBranchSet": _node_gmm_branch_set,
    "GmmLogicTreeBranch": _node_gmm_branch,
}


# ---------------------------------------------------------------------------
# Root query
# ---------------------------------------------------------------------------


@strawberry.type(name="QueryRoot", description="This is the entry point for all graphql query operations.")
class Query:
    @strawberry.field
    def node(self, id: Annotated[strawberry.ID, strawberry.argument(description=_ID_DESCRIPTION)]) -> Node | None:  # noqa: A002
        type_name, internal = from_global_id(id)
        resolver = _NODE_DISPATCH.get(type_name)
        return resolver(internal) if resolver else None

    @strawberry.field(description="About this API ")
    def about(self) -> str | None:
        return f"Hello, I am nshm_model_graphql_api, version: {__version__}!"

    @strawberry.field(description="API version string")
    def version(self) -> str | None:
        return __version__

    @strawberry.field
    def current_model_version(self) -> str | None:
        return data.current_version()

    @strawberry.field
    def get_models(self) -> list[NshmModel | None] | None:
        return [
            NshmModel(version=model.version, title=model.title)
            for model in (data.get_model_by_version(v) for v in data.all_model_versions())
        ]

    @strawberry.field
    def get_model(self, version: str | None = strawberry.UNSET) -> NshmModel | None:
        # UNSET when the client omits `version`; data.get_model treats falsy as "default model".
        return _build_nshm_model(data.get_model(version or None))


schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(auto_camel_case=False),
)
