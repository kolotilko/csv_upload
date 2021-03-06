"""
Файл содержит скрипты представлений
"""
import os

from app import flask_app
from flask import request, render_template, url_for, jsonify
from werkzeug.utils import secure_filename

from app.celery_run import celery_app
from app.tasks import upload_from_link, upload_from_disk
import uuid


@flask_app.route('/', methods=['GET'])
def index():
    """
    Представление главной страницы

    :return: Главная страница с формой для загрузки файла
    """
    if request.method == 'GET':
        return render_template('index.html')


@flask_app.route('/uploadfile', methods=['POST'])
def uploadfile():
    """
    Представление для начала загрузки файла. При нажатии на кнопку на главной странице
    отправляется запрос на данное представление. В зависимости от того, ввёл пользователь ссылку на файл
    или выбрал файл для загрузки в очередь Сelery добавляется соответствующая задача.

    :return: Возвращает статус 202 успешном добавлении задач в очередь
    """

    file = request.files['file']
    # Если в форме нет файл, то запускается скачивание по ссылке
    if not file.filename:
        task = upload_from_link.delay(request.form['url_text'])
    else:

        filename = secure_filename(file.filename)
        # Сохранение файла на диск
        file_path = os.path.join(flask_app.config['UPLOAD_FOLDER'], filename + str(uuid.uuid4()))
        file.save(file_path)
        file.close()
        task = upload_from_disk.delay(file_path)
    return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  task_id=task.id),
                              'err_message': ''}


@flask_app.route('/status/<task_id>')
def taskstatus(task_id):
    """
    Представление по task_id определяет статус задачи и возвращает информацию о его состоянии

    :param guid task_id: Идентификатор задачи в celery.
    :return: JSON объект, содержащий информация о состоянии задачи
    """
    task = celery_app.AsyncResult(task_id)
    # Задача в очереди
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0.5,
            'total': 1,
            'status': 'В очереди'
        }
    # Задача выполняется и из неё можно получить данные о процессе выполнения
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    # Скрипт выполнения задачи вызвал исключение
    else:
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),
        }
    return jsonify(response)
