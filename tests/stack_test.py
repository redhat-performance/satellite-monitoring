from conftest import run_as


def test_grafana_target_running(user_service):
    assert user_service("grafana.target").is_running


def test_grafana_target_file_exists(server, user_home):
    f = server.file(f"{user_home}/.config/systemd/user/grafana.target")
    assert f.exists
    assert f.is_file


def test_grafana_target_wants_all_services(server, user_home):
    f = server.file(f"{user_home}/.config/systemd/user/grafana.target")
    content = f.content.decode()
    assert "WantedBy=default.target" in content


def test_all_quadlet_files_present(server, user_home):
    for container in ("valkey", "pcp", "grafana"):
        f = server.file(f"{user_home}/.config/containers/systemd/{container}.container")
        assert f.exists, f"Missing quadlet file for {container}"


def test_all_services_running(user_service):
    for service in ("valkey", "pcp", "grafana"):
        assert user_service(service).is_running, f"Service {service} is not running"
