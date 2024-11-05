#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#
import pathlib

from k8s_test_harness import harness
from k8s_test_harness.util import constants, env_util, k8s_util

IMG_PLATFORM = "amd64"
IMG_NAME = "multus"
INSTALL_NAME = "multus-cni"


def test_multus_deployment(tmp_path: pathlib.Path, module_instance: harness.Instance):
    rock = env_util.get_build_meta_info_for_rock_version(IMG_NAME, "v3.8", IMG_PLATFORM)

    clone_path = tmp_path / "multus"
    clone_path.mkdir()

    clone_command = [
        "git",
        "clone",
        "https://github.com/k8snetworkplumbingwg/helm-charts",
        "--depth",
        "1",
        str(clone_path.absolute()),
    ]
    module_instance.exec(clone_command)

    chart_path = clone_path / "multus"

    helm_command = k8s_util.get_helm_install_command(
        name="multus-cni",
        chart_name=str(chart_path.absolute()),
        images=[k8s_util.HelmImage(uri=rock.image)],
        namespace=constants.K8S_NS_KUBE_SYSTEM,
    )
    module_instance.exec(helm_command)

    k8s_util.wait_for_daemonset(
        module_instance, f"{INSTALL_NAME}-multus-ds", constants.K8S_NS_KUBE_SYSTEM
    )

    # Sanity check: make sure there isn't an error in Pebble that it couldn't start the service.
    process = module_instance.exec(
        [
            "k8s",
            "kubectl",
            "logs",
            "-n",
            constants.K8S_NS_KUBE_SYSTEM,
            f"daemonset.apps/{INSTALL_NAME}-multus-ds",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert '(Start service "multus") failed' not in process.stdout
