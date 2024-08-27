def test_homepage(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'<title>' in response.data  # Check for something you know exists
    # Optionally, check for a specific HTML element or text
    # assert b'Some known text' in response.data