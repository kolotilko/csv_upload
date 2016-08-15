from urllib.request import urlopen

import pandas as pd

from app.celery_run import celery_app
from app.models import Category
from app import db
import csv
import os
import tempfile

@celery_app.task(bind=True)
def upload_from_disk(self, file_path):
    total_bytes = os.path.getsize(file_path)
    file = open(file_path, 'r', encoding='utf-8')
    data = csv.DictReader(file, delimiter='\t')
    viewed_bytes = 0
    for line in data:
        for col in line:
            viewed_bytes += len(line[col])
        category = Category(category_lvl_1=line['categories_id_lvl2'])
        db.session.add(category)
        self.update_state(state='PROGRESS',
                          meta={'current': viewed_bytes, 'total': total_bytes,
                                'status': 'Processing'})
    db.session.commit()
    file.close()
    os.remove(file_path)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@celery_app.task(bind=True)
def upload_from_link(self, link):
    remote_file = urlopen(link)
    total_bytes = int(remote_file.getheader('Content-Length'))
    file = tempfile.NamedTemporaryFile(mode='r+', encoding='utf-8')
    viewed_bytes = 0
    for line in remote_file:
        viewed_bytes += len(line)
        file.write(line.decode('utf-8'))
        self.update_state(state='PROGRESS',
                          meta={'current': viewed_bytes, 'total': 2 * total_bytes,
                                'status': 'Writing file on disk'})
    remote_file.close()
    file.seek(0)
    data = csv.DictReader(file, delimiter='\t')
    viewed_bytes = 0
    for line in data:
        for col in line:
            viewed_bytes += len(line[col])
        category = Category(category_lvl_1='')
        db.session.add(category)
        self.update_state(state='PROGRESS',
                          meta={'current': (total_bytes + viewed_bytes), 'total': 2*total_bytes,
                                'status': 'Parsing CSV file'})

    db.session.commit()
    file.close()

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@celery_app.task()
def add(x,y):
    return x + y
