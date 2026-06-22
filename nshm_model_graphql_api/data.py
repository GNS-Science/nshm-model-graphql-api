"""Data-access layer over the nzshm-model library (graphene-free).

Thin, cached wrappers around `nzshm_model` dataclasses — the typed data layer the
Strawberry schema projects into GraphQL types. See docs/MIGRATION_LOG.md (Phase 2
design note) for why we reuse nzshm-model's dataclasses rather than mirroring them
into pydantic.

These mirror the helpers in the legacy `schema/` package exactly (same lookups,
same lru_cache, same assertions) so behaviour is identical during the migration.
"""

import json
from functools import lru_cache

import nzshm_model as nm
from nzshm_model.logic_tree.source_logic_tree import logic_tree as _slt

# Source-type classes, re-exported for union classification in the schema layer.
InversionSource = _slt.InversionSource
DistributedSource = _slt.DistributedSource


def all_model_versions() -> list[str]:
    return nm.all_model_versions()


def current_version() -> str:
    return nm.CURRENT_VERSION


def get_model(version: str | None = None):
    """Fetch a model by version, or the default model when version is falsy."""
    return nm.get_model_version(version) if version else nm.get_model_version()


@lru_cache
def get_model_by_version(model_version: str):
    """Caching wrapper around nm.get_model_version."""
    return nm.get_model_version(model_version)


@lru_cache
def get_source_branch_set(model_version: str, short_name: str):
    slt = get_model_by_version(model_version).source_logic_tree
    for bs in slt.branch_sets:
        if bs.short_name == short_name:
            return bs
    assert 0, f"branch set {short_name} was not found"  # pragma: no cover


@lru_cache
def get_source_branch(model_version: str, short_name: str, tag: str):
    branch_set = get_source_branch_set(model_version, short_name)
    for ltb in branch_set.branches:
        if ltb.tag == tag:
            return ltb
    assert 0, f"branch with {tag} was not found"  # pragma: no cover


@lru_cache
def get_gmm_branch_set(model_version: str, short_name: str):
    glt = get_model_by_version(model_version).gmm_logic_tree
    for bs in glt.branch_sets:
        if bs.short_name == short_name:
            return bs
    assert 0, f"branch set {short_name} was not found"  # pragma: no cover


@lru_cache
def get_gmm_branch(model_version: str, branch_set_short_name: str, gsim_name: str, gsim_args: str):
    branch_set = get_gmm_branch_set(model_version, branch_set_short_name)
    for ltb in branch_set.branches:
        if (ltb.gsim_name == gsim_name) and (ltb.gsim_args == json.loads(gsim_args)):
            return ltb
    assert 0, f"branch with gsim_name: {gsim_name} gsim_args: {gsim_args} was not found"  # pragma: no cover
