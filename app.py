import os
from flask import Flask, request, render_template, session, flash, redirect, \
    url_for, jsonify
from tasks import upload_from_link, upload_from_disk

from werkzeug.utils import secure_filename

from celery_run import celery_app


UPLOAD_FOLDER = 'C:/lamoda_new/files'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top-secret!'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = 'flask@example.com'

# Celery configuration
# app.config['CELERY_BROKER_URL'] = 'amqp://guest@localhost//'
# app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost'
# app.config['CELERY_TASK_SERIALIZER'] = 'pickle'
#
#
# # Initialize extensions
# celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'], include=['app.tasks'])
# celery.conf.update(app.config)




@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html', email=session.get('email', ''))
    email = request.form['email']
    session['email'] = email

    return redirect(url_for('index'))


@app.route('/uploadfile', methods=['POST'])
def uploadfile():
    if request.form['url_text']:
        task = upload_from_link.delay(request.form['url_text'])
    else:
        file = request.files['file']
        filename = secure_filename(file.filename)

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        task = upload_from_disk.delay(file_path)
    return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  task_id=task.id)}


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = celery_app.AsyncResult(task_id)
    print(task.state)
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


if __name__ == '__main__':
    app.run(debug=True)