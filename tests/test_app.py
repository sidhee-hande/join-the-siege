import os
from io import BytesIO

import pytest
from src.app import app, allowed_file

API_TOKEN = os.getenv("API_TOKEN")

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {API_TOKEN}"}

@pytest.mark.parametrize("filename, expected", [
    ("file.pdf", True),
    ("file.png", True),
    ("file.jpg", True),
    ("file.doc", False),
    ("file", False),
])
def test_allowed_file_extension_check(filename, expected):
    assert allowed_file(filename) == expected

def test_classify_file_missing_file_field(client, auth_headers):
    response = client.post('/classify_file', headers=auth_headers)
    assert response.status_code == 400
    assert response.get_json()["error"] == "No file part in the request"

def test_classify_file_empty_filename(client, auth_headers):
    data = {'file': (BytesIO(b""), '')}
    response = client.post('/classify_file', headers=auth_headers, data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert response.get_json()["error"] == "No selected file"

def test_classify_file_success(client, mocker, auth_headers):
    mocker.patch('src.app.classify_file', return_value=('invoice', 1200, 0.10))
    data = {'file': (BytesIO(b"fake content"), 'file.pdf')}
    response = client.post('/classify_file', headers=auth_headers, data=data, content_type='multipart/form-data')

    assert response.status_code == 200
    assert response.is_json
    json_data = response.get_json()
    assert json_data["file_class"] == "invoice"
    assert json_data["cost_in_microdollars"] == 1200
    assert json_data["time_in_seconds"] == 0.10

def test_classify_file_unauthorized(client):
    data = {'file': (BytesIO(b"test"), 'file.pdf')}
    response = client.post('/classify_file', data=data, content_type='multipart/form-data')
    assert response.status_code == 401 or response.status_code == 403
