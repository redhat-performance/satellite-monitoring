from conftest import run_as


def test_valkey_quadlet_file_exists(server, user_home):
    f = server.file(f"{user_home}/.config/containers/systemd/valkey.container")
    assert f.exists
    assert f.is_file


def test_valkey_service_running(user_service):
    assert user_service("valkey").is_running


def test_valkey_ping(server, user):
    result = run_as(server, user, "podman exec valkey valkey-cli ping")
    assert result.succeeded
    assert result.stdout.strip() == "PONG"
