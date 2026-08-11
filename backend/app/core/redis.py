import redis

from app.core.config import settings

_redis_client: redis.Redis | None = None


def init_redis() -> redis.Redis:
    global _redis_client
    _redis_client = redis.Redis.from_url(
        settings.redis_url, decode_responses=True, socket_connect_timeout=3
    )
    return _redis_client


def get_redis_client() -> redis.Redis:
    if _redis_client is None:
        return init_redis()
    return _redis_client


def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        _redis_client.close()
        _redis_client = None
