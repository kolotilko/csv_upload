from __future__ import absolute_import
from celery import Celery

celery_app = Celery('celery_run',
                broker='amqp://guest@localhost//',
                backend='redis://localhost',
                include=['tasks'])


celery_app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)
