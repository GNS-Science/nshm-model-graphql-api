import os
from importlib import reload

import nzshm_model_graphql_api.settings

"""
These tests check for the configuration that has been found to work on
both AWS and locally, adressing https://github.com/GNS-Science/nshm-model-graphql-api/issues/10

It seems odd, but it seems that whitenoise community are a bit
confused about the correct approach currently.

ref https://github.com/evansd/whitenoise/issues/271
"""


def test_static_with_debug_true():
    os.environ["DEBUG"] = "1"
    reload(nzshm_model_graphql_api.settings)
    assert nzshm_model_graphql_api.settings.STATIC_URL == "static/"


def test_static_with_debug_false():
    os.environ["DEBUG"] = ""
    reload(nzshm_model_graphql_api.settings)
    assert nzshm_model_graphql_api.settings.STATIC_URL == "static/"


def test_static_with_debug_true_and_aws():
    os.environ["DEBUG"] = "1"
    os.environ["DEPLOYMENT_STAGE"] = "FOO"
    reload(nzshm_model_graphql_api.settings)
    assert nzshm_model_graphql_api.settings.STATIC_URL == "static/"


def test_static_with_debug_false_and_aws():
    """The typical AWS configuration for DEV, TEST & PROD stages."""
    os.environ["DEBUG"] = ""
    os.environ["DEPLOYMENT_STAGE"] = "FOO"
    reload(nzshm_model_graphql_api.settings)
    assert nzshm_model_graphql_api.settings.STATIC_URL == "FOO/static/"
