import pytest

@pytest.mark.skipif(not connect.dbuser, reason="No database connection available")
def test_homepage(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome' in response.data