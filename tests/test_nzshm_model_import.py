#! test_module_import
import nzshm_model
import pytest


def test_current_version():
    assert nzshm_model.CURRENT_VERSION == "NSHM_v1.0.4"


def test_available_versions():
    assert len(nzshm_model.versions) == 2


@pytest.mark.parametrize(
    "model, model_version",
    [("NSHM_v1.0.0", "NSHM_v1.0.0"), ("NSHM_v1.0.4", "NSHM_v1.0.4")],
)
def test_version_config(model, model_version):
    mod = nzshm_model.get_model_version(model)
    assert mod.version == model_version
