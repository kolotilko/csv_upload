"""
Файл со скриптами задач для Celery
"""
from urllib.request import urlopen
from urllib.error import URLError
import zipfile
from app.celery_run import celery_app
from app.models import Category
from app import db
import csv
import os
import tempfile
from sqlalchemy.exc import SQLAlchemyError
SIZE_INSERTED_CHUNK = 1000


@celery_app.task(bind=True)
def upload_from_disk(self, file_path):
    """
    Загружает в БД данные из файла отправленного через форму.
    Если пришёл zip-архив, то он разархивируется и проверяется на корректность
    Для разбора csv-файла используется стандартная библиотека csv
    Файл после загрузки удаляется.

    :var total_bytes: Количество байт в файле. Нужно для расчёта процента выполненной работы.
    :param object self: Объект, содержащий задачу. Нужен для обновления состояния задачи
    :param os.path file_path: Путь к файлу с данными
    :return: Возвращает сообщение об успешном заверешении задачи.
    """
    total_bytes = os.path.getsize(file_path)
    #Разбор zip-архива
    if zipfile.is_zipfile(file_path):
        try:
            with zipfile.ZipFile(file_path, 'r') as archive:
                data_file, total_bytes = get_data_file_from_archive(self, archive)
                upload_progress = 0.75
        except zipfile.BadZipFile:
            os.remove(file_path)
            raise Exception('Неправильный формат архива')
    else:
        data_file = open(file_path, 'r', encoding='utf-8')
        upload_progress = 0.5
    try:
        #Загрузка данных в БД
        data = csv.DictReader(data_file, delimiter='\t')
        upload_to_database(self, data, total_bytes, upload_progress)
    except SQLAlchemyError:
        raise Exception('Ошибка базы данных')
    except csv.Error:
        raise Exception('Неправильный формат csv-файла')
    except UnicodeDecodeError:
        raise Exception('Ошибка кодировки')
    finally:
        data_file.close()
        os.remove(file_path)
    return {'current': 100, 'total': 100, 'status': 'Загрузка и разбор успешно заверешены'}


@celery_app.task(bind=True)
def upload_from_link(self, link):
    """
    Функция для загрузки и разбора файла по ссылке. Скачивает и записывает файл во временный файл.
    Если пришёл zip-архив, то он разархивируется.
    После этого происходит итерация по скачанному файлу и запись данных в БД.

    :var total_bytes: Количество байт в загружаемом файле
    :param object self: Объект задачи. Нужен для обновления статуса задачи
    :param str link: Ссылка на файл с данным
    :return: Информацию об успешном завершении загрузки и разбора файла.
    """
    #Открытие ссылки
    try:
        remote_file = urlopen(link)
        total_bytes = int(remote_file.getheader('Content-Length'))
        application_type = remote_file.getheader('Content-Type')
    except ValueError:
        raise Exception('Неправильная ссылка')
    except (URLError, TypeError):
        raise Exception('Ошибка соединения')
    #Если по ссылке архив, то распаковываем его
    if application_type == 'application/zip':
        archive_file = tempfile.TemporaryFile(mode='rb+')
        viewed_bytes = 0
        for i, line in enumerate(remote_file):
            viewed_bytes += len(line)
            archive_file.write(line)
            if i % SIZE_INSERTED_CHUNK == 0:
                self.update_state(state='PROGRESS',
                                  meta={'current': viewed_bytes, 'total': 2 * total_bytes,
                                        'status': 'Загрузка файла'})
        try:
            archive = zipfile.ZipFile(archive_file, 'r')
            data_file, total_bytes = get_data_file_from_archive(self, archive)
        except zipfile.BadZipFile:
            raise Exception('Неправильный формат zip-архива')

        finally:
            archive_file.close()
        upload_progress = 0.75
    else:
        #Записываем данные по ссылке во временный файл
        data_file = tempfile.NamedTemporaryFile(mode='r+', encoding='utf-8')
        viewed_bytes = 0
        for i, line in enumerate(remote_file):
            viewed_bytes += len(line)
            data_file.write(line.decode('utf-8'))
            if i % SIZE_INSERTED_CHUNK == 0:
                self.update_state(state='PROGRESS',
                                  meta={'current': viewed_bytes, 'total': 2 * total_bytes,
                                        'status': 'Загрузка файла'})
        remote_file.close()
        data_file.seek(0)
        upload_progress = 0.5

    #Загрузка данных в БД
    data = csv.DictReader(data_file, delimiter='\t')
    try:
        upload_to_database(self, data, total_bytes, upload_progress)
    except SQLAlchemyError:
        raise Exception('Ошибка базы данных')
    except csv.Error:
        raise Exception('Неправильный формат csv-файла')
    except UnicodeDecodeError:
        raise Exception('Ошибка кодировки')
    finally:
        data_file.close()

    return {'current': 100, 'total': 100, 'status': 'Загрузка и разбор успешно завершены',
            'result': 42}


def upload_to_database(task, data, total_bytes, progress):
    """
    Функция для загрузки данных в БД. Итерирует по данным и  каждые SIZE_INSERTED_CHUNK записей
    создаёт insert-инструкции. После просмотра все записей делает commit транзкации в БД

    :param object task: Объект задачи необходимы для обновления состояния задачи
    :param iterator data: Итератор по данным csv файла
    :param float progress: Показатель текущего прогресса
    :param total_bytes: Количество байт в данных. Необходимо для расчёта прогресса выполнения задачи
    :param total_bytes: Количество байт в данных. Необходимо для расчёта прогресса выполнения задачи
    :return:
    """
    viewed_bytes = 0
    records_list = []
    #Цикл по строкам
    for index, line in enumerate(data):
        for col in line:
            viewed_bytes += len(line[col].encode('utf-8'))
        #Создаём пакет инструкция для вставки
        if index % SIZE_INSERTED_CHUNK == 0:
            db.session.bulk_insert_mappings(Category, records_list)
            records_list = []
        records_list.append(line)
        #Обновляем информацию о состоянии задачи
        if index % SIZE_INSERTED_CHUNK == 0:
            task.update_state(state='PROGRESS',
                              meta={'current': (progress*total_bytes + (1-progress)*viewed_bytes), 'total': total_bytes,
                                    'status': 'Разбор файла'})
    db.session.bulk_insert_mappings(Category, records_list)
    db.session.commit()


def get_data_file_from_archive(task, archive):
    """
    Функция прсоматривает загруженный архив. Если в нём содержится больше одного csv файла, то генерируется исключение

    :param object task:Объект задачи. Нужен для обновления статуса задачи
    :param File archive: ссылка на архив
    :return: Вовращает количество байт в файле и файл с разархивированным содержанием
    """
    #Получение списка файлов в архиве. Не учитываются файлы, содержаище __MACOSX в названии
    csv_file_list = list(filter(lambda x: '__MACOSX' not in x.filename, archive.infolist()))
    #Если файлов больше одного, то генериутеся ошибка
    if len(csv_file_list) > 1:
        raise zipfile.BadZipFile
    else:
        total_bytes = csv_file_list[0].file_size
        binary_file = archive.open(csv_file_list[0])
        data_file = tempfile.NamedTemporaryFile(mode='r+', encoding='utf-8')
        viewed_bytes = 0
        #Записываем бинарные данные во временные файл в понятном csv парсера формате
        for i, line in enumerate(binary_file):
            viewed_bytes += len(line)
            data_file.write(line.decode('utf-8'))
            if i % SIZE_INSERTED_CHUNK == 0:
                task.update_state(state='PROGRESS',
                                  meta={'current': total_bytes + viewed_bytes // 2, 'total': 2 * total_bytes,
                                        'status': 'Распаковка архива'})
        #Перход к началу файла
        data_file.seek(0)
        binary_file.close()
    return data_file, total_bytes
