from urllib.request import urlopen
import cProfile


from app.celery_run import celery_app
from app.models import Category
from app import db
import csv
import os
import tempfile

SIZE_INSERTED_CHUNK = 1000


@celery_app.task(bind=True)
def upload_from_disk(self, file_path):
    total_bytes = os.path.getsize(file_path)
    file = open(file_path, 'r', encoding='utf-8')
    data = csv.DictReader(file, delimiter='\t')
    upload_to_database(self, data, total_bytes)
    file.close()
    os.remove(file_path)
    return {'current': 100, 'total': 100, 'status': 'Загрузка и разбор заверешены'}


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
                                'status': 'Загрузка файла'})
    remote_file.close()
    file.seek(0)
    data = csv.DictReader(file, delimiter='\t')
    upload_to_database(self, data, total_bytes)
    file.close()

    return {'current': 100, 'total': 100, 'status': 'Загрузка и разбор завершены',
            'result': 42}


def upload_to_database(task, data, total_bytes):
    viewed_bytes = 0
    count_bytes = 0
    add_rec = 0
    upd_state = 0
    records_list = []
    for index, line in enumerate(data):
        for col in line:
            viewed_bytes += len(line[col].encode('utf-8'))
        if index % SIZE_INSERTED_CHUNK == 0:
            db.session.bulk_insert_mappings(Category, records_list)
            records_list = []
        records_list.append(line)
        if index % SIZE_INSERTED_CHUNK == 0:
            task.update_state(state='PROGRESS',
                              meta={'current': (viewed_bytes + total_bytes), 'total': 2*total_bytes,
                                    'status': 'Разбор файла'})
    db.session.bulk_insert_mappings(Category, records_list)
    db.session.commit()
