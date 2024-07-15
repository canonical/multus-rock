# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
#
#

import random
import pytest
import string
import subprocess

from charmed_kubeflow_chisme.rock import CheckRock


def check_image_paths(image, paths):
    for path in paths:
        subprocess.run(
            [
                "docker", "run", image,
                "ls", "-l", path
            ],
            check=True,
        )


def test_rock():
    """Test rock."""
    check_rock = CheckRock("rockcraft.yaml")
    rock_image = check_rock.get_name()
    rock_version = check_rock.get_version()
    LOCAL_ROCK_IMAGE = f"{rock_image}:{rock_version}"

    # check rock filesystem
    check_image_paths(
        LOCAL_ROCK_IMAGE,
        [
            "/entrypoint.sh",
            "/usr/src/multus-cni/bin/multus",
            "/usr/src/multus-cni/LICENSE",
        ])
