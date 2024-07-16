#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#

import os
import subprocess

from charmed_kubeflow_chisme.rock import CheckRock
from k8s_test_harness.util import docker_util


def test_entrypoint_helpstring():
    image = os.getenv("ROCK_MULTUS_V4_0_2")
    assert image is not None, "ROCK_MULTUS_V4_0_2 is not set"
    # "/thin_entrypoint --help" shows the help string but has a
    # non-zero exit code (1).
    docker_run = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "/thin_entrypoint", image, "--help"],
        capture_output=True,
        check=False,
        text=True,
    )
    assert "--multus-conf-file string" in docker_run.stderr


def test_image_files():
    """Test rock."""
    check_rock = CheckRock(os.path.dirname(__file__) + "/../../v4.0.2/rockcraft.yaml")
    rock_image = check_rock.get_name()
    rock_version = check_rock.get_version()
    LOCAL_ROCK_IMAGE = f"{rock_image}:{rock_version}"

    # check rock filesystem
    docker_util.ensure_image_contains_paths(
        LOCAL_ROCK_IMAGE,
        [
            "/install_multus",
            "/thin_entrypoint",
            "/usr/src/multus-cni/LICENSE",
            "/usr/src/multus-cni/bin/install_multus",
            "/usr/src/multus-cni/bin/thin_entrypoint",
            "/usr/src/multus-cni/bin/multus",
            "/usr/src/multus-cni/bin/multus-daemon",
            "/usr/src/multus-cni/bin/multus-shim",
        ],
    )
