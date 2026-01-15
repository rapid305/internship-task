import taskiq_fastapi
from taskiq_aio_pika import AioPikaBroker
from taskiq_redis import RedisAsyncResultBackend

from app.settings import settings

result_backend = RedisAsyncResultBackend(
    redis_url=settings.get("REDIS.URL"),
)

broker = AioPikaBroker(
    url=settings.get("TASKIQ.AMQP_URL"),
).with_result_backend(result_backend)

taskiq_fastapi.init(broker, "app.main:app")
