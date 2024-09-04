def test_depot_info(client):
    """Test that the depot information is correctly displayed"""
    response = client.get('/depot')
    assert response.status_code == 200
    assert b"Depot 1" in response.data
    assert b"Location 1" in response.data
    assert b"Manager 1" in response.data