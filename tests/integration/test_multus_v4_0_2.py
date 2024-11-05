#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#
from k8s_test_harness import harness
from k8s_test_harness.util import constants, env_util, k8s_util

IMG_PLATFORM = "amd64"
IMG_NAME = "multus"
INSTALL_NAME = "multus-cni"


def test_multus_deployment(module_instance: harness.Instance):
    rock = env_util.get_build_meta_info_for_rock_version(
        IMG_NAME, "v4.0.2", IMG_PLATFORM
    )

    # This helm chart requires the registry to be separated from the image.
    rock_image = rock.image
    registry = "docker.io"
    parts = rock_image.split("/")
    if len(parts) > 1:
        registry = parts[0]
        rock_image = "/".join(parts[1:])

    helm_command = k8s_util.get_helm_install_command(
        name=INSTALL_NAME,
        chart_name="oci://registry-1.docker.io/bitnamicharts/multus-cni",
        images=[k8s_util.HelmImage(uri=rock_image)],
        namespace=constants.K8S_NS_KUBE_SYSTEM,
        set_configs=[f"image.registry={registry}"],
        chart_version="2.1.7",
    )
    module_instance.exec(helm_command)

    k8s_util.wait_for_daemonset(
        module_instance, INSTALL_NAME, constants.K8S_NS_KUBE_SYSTEM
    )

    # Sanity check: make sure there isn't an error in Pebble that it couldn't start the service.
    process = module_instance.exec(
        [
            "k8s",
            "kubectl",
            "logs",
            "-n",
            constants.K8S_NS_KUBE_SYSTEM,
            f"daemonset.apps/{INSTALL_NAME}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert '(Start service "multus") failed' not in process.stdout
