import os

import pytest
import testinfra


SSH_CONFIG = './.tmp/ssh-config'

# Controls how run_as() switches to the rootless user. Set via environment
# variable so the method can be swapped without touching any test:
#
#   GRAFANA_PCP_RUN_AS_METHOD=runuser      (default) sudo-free, propagates exit codes
#   GRAFANA_PCP_RUN_AS_METHOD=machinectl  full login session, XDG auto-set
RUN_AS_METHOD = os.environ.get("GRAFANA_PCP_RUN_AS_METHOD", "runuser")


def run_as(host, user, cmd):
    """Run cmd on host as user, using the configured RUN_AS_METHOD."""
    escaped = cmd.replace("'", "'\\''")
    if RUN_AS_METHOD == "machinectl":
        return host.run(f"machinectl shell {user}@ /bin/bash -c '{escaped}'")
    else:  # runuser (default)
        xdg = f"XDG_RUNTIME_DIR=/run/user/$(id -u {user})"
        return host.run(f"runuser -l {user} -s /bin/bash -c 'export {xdg}; {escaped}'")


def get_user_home(host, user):
    result = host.run(f"getent passwd {user}")
    assert result.succeeded
    return result.stdout.split(':')[5].strip()


class UserService:
    """Testinfra-compatible wrapper for a systemd user-scope service."""

    def __init__(self, host, user, name):
        self._host = host
        self._user = user
        self._name = name

    def _run(self, cmd):
        return run_as(self._host, self._user, cmd)

    @property
    def is_running(self):
        return self._run(f"systemctl --user is-active {self._name}").rc == 0

    @property
    def is_enabled(self):
        return self._run(f"systemctl --user is-enabled {self._name}").rc == 0

    @property
    def exists(self):
        # systemctl --user status exits 4 when the unit is not found
        return self._run(f"systemctl --user status {self._name}").rc != 4


@pytest.fixture(scope="module")
def server():
    yield testinfra.get_host('paramiko://grafana-pcp', sudo=True, ssh_config=SSH_CONFIG)


@pytest.fixture(scope="module")
def user():
    """The rootless user running the grafana-pcp services."""
    return "grafana-pcp"


@pytest.fixture(scope="module")
def user_home(server, user):
    return get_user_home(server, user)


@pytest.fixture(scope="module")
def user_service(server, user):
    """Factory fixture: user_service("grafana") returns a UserService instance."""
    def _factory(name):
        return UserService(server, user, name)
    return _factory
