import pytest

from api import API
from constants import BASE_URL


@pytest.fixture
def api():
    return API()


@pytest.fixture
def client(api):
    return api.test_session()
