import pytest


def test_index_serves_registration_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'id="register-form"' in response.text


def test_index_only_allows_own_resources(client):
    response = client.get("/")

    assert "default-src 'self'" in response.headers["content-security-policy"]
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize("path", ["style.css", "app.js", "favicon.svg"])
def test_static_files_are_served(client, path):
    assert client.get(f"/static/{path}").status_code == 200


def test_api_documentation_keeps_working(client):
    assert client.get("/docs").status_code == 200
