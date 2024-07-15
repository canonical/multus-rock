#
# Copyright 2024 Canonical, Ltd.
#
import os

from test_util import harness, util


def test_multus_deployment(module_instance: harness.Instance):
    helm_command = [
        "sudo", "k8s",
        "helm", "install", "multus-cni",
        "oci://registry-1.docker.io/bitnamicharts/multus-cni",
        "--version", "2.1.7",
        "--namespace", "kube-system",
    ]

    image_uri = os.getenv("ROCK_MULTUS_V4_0_2")
    assert image_uri is not None, "ROCK_MULTUS_V4_0_2 is not set"
    image_split = image_uri.split(":")

    helm_command += [
        "--set",
        f"image.repository={image_split[0]}",
        "--set",
        f"image.tag={image_split[1]}",
        "--set",
        "securityContext.runAsUser=584792",
    ]

    module_instance.exec(helm_command)

    util.stubbornly(retries=3, delay_s=1).on(module_instance).exec(
        [
            "sudo", "k8s",
            "kubectl", "rollout", "status",
            "daemonset", "multus-cni",
            "--namespace", "kube-system",
            "--timeout", "180s",
        ]
    )
