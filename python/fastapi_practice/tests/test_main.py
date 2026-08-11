from fastapi.testclient import TestClient
from fastapi_practice.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}

def test_protected_route_wrong_key():
    response = client.get("/protected", headers={"x-api-key": "wrongkey"})
    assert response.status_code == 401

def test_protected_route_correct_key():
    response = client.get("/protected", headers={"x-api-key": "mysecretkey123"})
    assert response.status_code == 200