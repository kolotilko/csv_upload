import random

import pandas as pd
from urllib.request import urlopen
from celery_run import celery_app

@celery_app.task(bind=True)
def upload_from_disk(self, file_path):
    file = pd.read_csv(file_path, sep='\t', header=0, encoding='utf-8')
    for i, line in enumerate(file.iterrows()):
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': file.shape[0],
                                'status': 'Processing'})

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@celery_app.task(bind=True)
def upload_from_link(self, link):
    remote_file = urlopen(link)
    # for line in remote_file:
    #     print(line)
    file = pd.read_csv(remote_file, sep='\t', header=0, encoding='utf-8')
    total = random.randint(10, 50)
    for i, line in enumerate(file.iterrows()):
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': file.shape[0],
                                'status': 'Processing'})

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@celery_app.task()
def add(x,y):
    return x + y
