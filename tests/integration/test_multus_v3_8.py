#
# Copyright 2024 Canonical, Ltd.
#
import os
import pathlib

from test_util import harness, util


def test_multus_deployment(
        tmp_path: pathlib.Path,
        module_instance: harness.Instance):
    clone_path = tmp_path / "multus"
    clone_path.mkdir()

    clone_command = [
        "git", "clone", "https://github.com/k8snetworkplumbingwg/helm-charts",
        "--depth", "1",
        str(clone_path.absolute())
    ]
    module_instance.exec(clone_command)

    chart_path = clone_path / 'multus'

    helm_command = [
        "sudo", "k8s",
        "helm", "install", "multus-cni",
        str(chart_path.absolute()),
        "--namespace", "kube-system",
    ]

    image_uri = os.getenv("ROCK_MULTUS_V3_8")
    assert image_uri is not None, "ROCK_MULTUS_V3_8 is not set"
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
            "daemonset", "multus-cni-multus-ds",
            "--namespace", "kube-system",
            "--timeout", "60s",
        ]
    )
