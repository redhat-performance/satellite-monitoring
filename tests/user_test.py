from conftest import run_as


def test_user_exists(server, user):
    assert server.user(user).exists


def test_user_home_exists(server, user_home):
    d = server.file(user_home)
    assert d.exists
    assert d.is_directory


def test_user_lingering_enabled(server, user):
    linger_file = server.file(f"/var/lib/systemd/linger/{user}")
    assert linger_file.exists


def test_user_subuid_entry(server, user):
    subuid = server.file("/etc/subuid")
    assert subuid.contains(f"^{user}:")


def test_user_subgid_entry(server, user):
    subgid = server.file("/etc/subgid")
    assert subgid.contains(f"^{user}:")


def test_user_quadlet_dir_exists(server, user_home):
    d = server.file(f"{user_home}/.config/containers/systemd")
    assert d.exists
    assert d.is_directory


def test_user_systemd_dir_exists(server, user_home):
    d = server.file(f"{user_home}/.config/systemd/user")
    assert d.exists
    assert d.is_directory


def test_xdg_runtime_dir_exists(server, user):
    result = run_as(server, user, "ls $XDG_RUNTIME_DIR")
    assert result.succeeded
