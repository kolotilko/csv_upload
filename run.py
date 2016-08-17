'''
Скрипт запуска приложения.
'''
from app import flask_app
flask_app.run(debug=True, host='0.0.0.0')
