#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#

from k8s_test_harness.util import docker_util, env_util

# In the future, we may also test ARM
IMG_PLATFORM = "amd64"
IMG_NAME = "multus"

V3_8_EXPECTED_FILES = [
    "/entrypoint.sh",
    "/usr/src/multus-cni/bin/multus",
    "/usr/src/multus-cni/LICENSE",
]

# Just a line that the help string is expected to contain
V3_8_EXPECTED_HELPSTR = "This is an entrypoint script for Multus CNI"

V4_0_2_EXPECTED_FILES = [
    "/install_multus",
    "/thin_entrypoint",
    "/usr/src/multus-cni/LICENSE",
    "/usr/src/multus-cni/bin/install_multus",
    "/usr/src/multus-cni/bin/thin_entrypoint",
    "/usr/src/multus-cni/bin/multus",
    "/usr/src/multus-cni/bin/multus-daemon",
    "/usr/src/multus-cni/bin/multus-shim",
]

V4_0_2_EXPECTED_HELPSTR = "--multus-conf-file string"


def test_multus_3_8():
    rock = env_util.get_build_meta_info_for_rock_version(IMG_NAME, "v3.8", IMG_PLATFORM)

    docker_run = docker_util.run_in_docker(rock.image, ["/entrypoint.sh", "--help"])
    assert V3_8_EXPECTED_HELPSTR in docker_run.stdout

    # check rock filesystem
    docker_util.ensure_image_contains_paths(rock.image, V3_8_EXPECTED_FILES)


def test_multus_4_0_2():
    rock = env_util.get_build_meta_info_for_rock_version(
        IMG_NAME, "v4.0.2", IMG_PLATFORM
    )

    # "/thin_entrypoint --help" shows the help string but has a
    # non-zero exit code (1).
    docker_run = docker_util.run_in_docker(
        rock.image, ["/thin_entrypoint", "--help"], check_exit_code=False
    )
    assert V4_0_2_EXPECTED_HELPSTR in docker_run.stderr

    # check rock filesystem
    docker_util.ensure_image_contains_paths_bare(rock.image, V4_0_2_EXPECTED_FILES)
