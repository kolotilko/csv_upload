"""
Скрипт создания объекта Celery.
В качестве брокера сообщений используется RabbitMQ. Для хранения результатов используется redis.
"""
from __future__ import absolute_import
from celery import Celery

CELERY_BROKER = 'amqp://guest@localhost//'
CELERY_BACKEND = 'redis://localhost'
celery_app = Celery('app.celery_run',
                    broker=CELERY_BROKER,
                    backend=CELERY_BACKEND,
                    include=['app.tasks'])

celery_app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)
