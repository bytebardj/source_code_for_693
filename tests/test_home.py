def test_homepage(client):
    response = client.get('/home')
    assert response.status_code == 200
    assert b'Welcome' in response.data