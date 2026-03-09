import json

from conftest import run_as


def test_grafana_quadlet_file_exists(server, user_home):
    f = server.file(f"{user_home}/.config/containers/systemd/grafana.container")
    assert f.exists
    assert f.is_file


def test_grafana_service_running(user_service):
    assert user_service("grafana").is_running


def test_grafana_api_healthy(server):
    result = server.run("curl -sf http://localhost:3000/api/health")
    assert result.succeeded
    body = json.loads(result.stdout)
    assert body.get("database") == "ok"


def test_grafana_pcp_plugin_enabled(server):
    result = server.run(
        "curl -sf -u admin:admin "
        "http://localhost:3000/api/plugins/performancecopilot-pcp-app/settings"
    )
    assert result.succeeded
    body = json.loads(result.stdout)
    assert body.get("enabled") is True
