#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#
import os
import subprocess

from charmed_kubeflow_chisme.rock import CheckRock
from k8s_test_harness.util import docker_util


def test_entrypoint_helpstring():
    image = os.getenv("ROCK_MULTUS_V3_8")
    assert image is not None, "ROCK_MULTUS_V3_8 is not set"
    docker_run = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "/entrypoint.sh", image, "--help"],
        capture_output=True,
        check=True,
        text=True,
    )
    assert "This is an entrypoint script for Multus CNI" in docker_run.stdout


def test_image_files():
    """Test rock."""
    check_rock = CheckRock(os.path.dirname(__file__) + "/../../v3.8/rockcraft.yaml")
    rock_image = check_rock.get_name()
    rock_version = check_rock.get_version()
    LOCAL_ROCK_IMAGE = f"{rock_image}:{rock_version}"

    # check rock filesystem
    docker_util.ensure_image_contains_paths(
        LOCAL_ROCK_IMAGE,
        [
            "/entrypoint.sh",
            "/usr/src/multus-cni/bin/multus",
            "/usr/src/multus-cni/LICENSE",
        ],
    )
