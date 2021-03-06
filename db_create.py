"""
Скрипт для создания схемы базы данных и папки для хранения миграций БД.
"""
import os.path

from migrate.versioning import api

from app import SQLALCHEMY_DATABASE_URI
from app import SQLALCHEMY_MIGRATE_REPO
from app import db

db.create_all()
if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
else:
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))
