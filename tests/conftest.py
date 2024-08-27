import pytest
from app import views
#

@pytest.fixture
def client():
    with views.test_client() as client:
        yield client