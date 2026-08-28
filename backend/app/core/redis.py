from redis.asyncio import Redis, ConnectionPool
from app.core.config import settings
from app.core.logging import logger

pool = None
use_mock_redis = False
mock_redis_client = None

try:
    pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        max_connections=20
    )
except Exception as e:
    logger.warning(f"Could not create Redis connection pool: {str(e)}. Falling back to mock Redis.")
    use_mock_redis = True

async def get_redis() -> Redis:
    """Get async Redis client from the shared connection pool, falling back to fakeredis if needed."""
    global use_mock_redis, mock_redis_client
    if use_mock_redis:
        if mock_redis_client is None:
            import fakeredis.aioredis
            mock_redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
            logger.info("Initialized in-memory Mock Redis (fakeredis).")
        return mock_redis_client
    try:
        return Redis(connection_pool=pool)
    except Exception as e:
        logger.warning(f"Failed to initialize Redis client: {str(e)}. Falling back to mock Redis.")
        use_mock_redis = True
        if mock_redis_client is None:
            import fakeredis.aioredis
            mock_redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        return mock_redis_client

async def test_redis_connection() -> bool:
    """Test connection to Redis."""
    global use_mock_redis
    try:
        if use_mock_redis:
            logger.warning("Using in-memory Mock Redis (fakeredis). Background tasks will be simulated.")
            return True
            
        client = await get_redis()
        ping_result = await client.ping()
        if ping_result:
            logger.info("Successfully connected to Redis.")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}. Switching to Mock Redis.")
        use_mock_redis = True
        return True

