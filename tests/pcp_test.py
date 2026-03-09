from conftest import run_as


def test_pcp_quadlet_file_exists(server, user_home):
    f = server.file(f"{user_home}/.config/containers/systemd/pcp.container")
    assert f.exists
    assert f.is_file


def test_pcp_service_running(user_service):
    assert user_service("pcp").is_running


def test_pmcd_responding(server, user):
    result = run_as(server, user, "podman exec pcp pminfo -v pmcd.numclients")
    assert result.succeeded


def test_pmproxy_responding(server):
    result = server.run("curl -sf http://localhost:44322/api/metric?names=pmcd.numclients")
    assert result.succeeded
