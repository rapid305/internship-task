import taskiq_fastapi
from taskiq_aio_pika import AioPikaBroker
from taskiq_redis import RedisAsyncResultBackend

from app.settings import settings

result_backend = RedisAsyncResultBackend(
    redis_url=settings.redis.url,
)

broker = AioPikaBroker(
    url=settings.taskiq.amqp_url,
).with_result_backend(result_backend)

taskiq_fastapi.init(broker, "app.main:app")
