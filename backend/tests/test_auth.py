def test_register_creates_user(client):
    response = client.post("/auth/register", json={"username": "lucas", "password": "senha1234"})

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "lucas"
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_username_fails(client):
    client.post("/auth/register", json={"username": "lucas", "password": "senha1234"})
    response = client.post("/auth/register", json={"username": "lucas", "password": "outrasenha"})

    assert response.status_code == 409