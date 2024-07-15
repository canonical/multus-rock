#
# Copyright 2024 Canonical, Ltd.
#
import logging
from pathlib import Path
from typing import Generator, List

import pytest
from test_util import config, harness, util

LOG = logging.getLogger(__name__)


def _harness_clean(h: harness.Harness):
    "Clean up created instances within the test harness."

    if config.SKIP_CLEANUP:
        LOG.warning(
            "Skipping harness cleanup. "
            "It is your job now to clean up cloud resources"
        )
    else:
        LOG.debug("Cleanup")
        h.cleanup()


@pytest.fixture(scope="module")
def h() -> harness.Harness:
    LOG.debug("Create harness for %s", config.SUBSTRATE)
    if config.SUBSTRATE == "local":
        h = harness.LocalHarness()
    elif config.SUBSTRATE == "lxd":
        h = harness.LXDHarness()
    elif config.SUBSTRATE == "multipass":
        h = harness.MultipassHarness()
    elif config.SUBSTRATE == "juju":
        h = harness.JujuHarness()
    else:
        raise harness.HarnessError(
            "TEST_SUBSTRATE must be one of: local, lxd, multipass, juju"
        )

    yield h

    _harness_clean(h)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "node_count: Mark a test to specify how many instance nodes need to be created\n"
        "disable_k8s_bootstrapping: By default, the first k8s node is bootstrapped. This marker disables that.",
    )


@pytest.fixture(scope="function")
def node_count(request) -> int:
    node_count_marker = request.node.get_closest_marker("node_count")
    if not node_count_marker:
        return 1
    node_count_arg, *_ = node_count_marker.args
    return int(node_count_arg)


@pytest.fixture(scope="function")
def disable_k8s_bootstrapping(request) -> int:
    return bool(request.node.get_closest_marker("disable_k8s_bootstrapping"))


@pytest.fixture(scope="function")
def instances(
    h: harness.Harness, node_count: int, tmp_path: Path, disable_k8s_bootstrapping: bool
) -> Generator[List[harness.Instance], None, None]:
    """Construct instances for a cluster.

    Bootstrap and setup networking on the first instance, if `disable_k8s_bootstrapping` marker is not set.
    """
    if not config.SNAP_CHANNEL:
        pytest.fail("Set TEST_SNAP_CHANNEL to the channel of the k8s snap to install.")

    if node_count <= 0:
        pytest.xfail("Test requested 0 or fewer instances, skip this test.")

    LOG.info(f"Creating {node_count} instances")
    instances: List[harness.Instance] = []

    for _ in range(node_count):
        # Create <node_count> instances and setup the k8s snap in each.
        instance = h.new_instance()
        instances.append(instance)
        util.setup_k8s_snap(instance)

    if not disable_k8s_bootstrapping:
        first_node, *_ = instances
        first_node.exec(["k8s", "bootstrap"])

    yield instances

    if config.SKIP_CLEANUP:
        LOG.warning("Skipping clean-up of instances, delete them on your own")
        return

    # Cleanup after each test.
    # We cannot execute _harness_clean() here as this would also
    # remove the module_instance.
    for instance in instances:
        h.delete_instance(instance.id)


@pytest.fixture(scope="module")
def module_instance(
    h: harness.Harness, tmp_path_factory: pytest.TempPathFactory,
    request
) -> Generator[harness.Instance, None, None]:
    """Constructs and bootstraps an instance that persists over a test session.

    Bootstraps the instance with all k8sd features enabled to reduce testing time.
    """
    LOG.info("Setup node and enable all features")

    instance = h.new_instance()
    util.setup_k8s_snap(instance)
    request.addfinalizer(lambda: util.purge_k8s_snap(instance))

    bootstrap_config_path = "/home/ubuntu/bootstrap-session.yaml"
    instance.send_file(
        (config.MANIFESTS_DIR / "bootstrap-session.yaml").as_posix(),
        bootstrap_config_path,
    )

    instance.exec(["k8s", "bootstrap", "--file", bootstrap_config_path])
    util.wait_until_k8s_ready(instance, [instance])
    util.wait_for_network(instance)
    util.wait_for_dns(instance)

    yield instance
