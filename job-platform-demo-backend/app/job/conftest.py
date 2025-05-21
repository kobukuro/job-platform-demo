import pytest
from core.throttling.redis import redis_client

@pytest.fixture(autouse=True)
def clear_redis():
    redis_client.flushall()
    yield
    redis_client.flushall()
