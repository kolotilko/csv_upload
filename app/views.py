import os

from app import flask_app
from flask import request, render_template, url_for, jsonify
from werkzeug.utils import secure_filename

from app.celery_run import celery_app
from app.tasks import upload_from_link, upload_from_disk


@flask_app.route('/', methods=['GET'])
def index():
    if request.method == 'GET':
        return render_template('index.html')



@flask_app.route('/uploadfile', methods=['POST'])
def uploadfile():
    if request.form['url_text']:
        task = upload_from_link.delay(request.form['url_text'])
    else:
        file = request.files['file']
        filename = secure_filename(file.filename)

        file_path = os.path.join(flask_app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        file.close()
        task = upload_from_disk.delay(file_path)
    return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  task_id=task.id)}


@flask_app.route('/status/<task_id>')
def taskstatus(task_id):
    task = celery_app.AsyncResult(task_id)
    print(task.state)
    print(task.info)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


