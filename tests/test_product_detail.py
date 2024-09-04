def test_product_detail(client, product_id, expected_name):
    """Test that individual product pages load correctly"""
    response = client.get(f'/product/{product_id}')
    assert response.status_code == 200
    assert expected_name.encode() in response.data