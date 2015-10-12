import os

class Config(object):
    DEBUG = False
    LOGGING_PATH = os.getenv('LOGGING_PATH', 'python_logging/logging.yaml')

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql+pg8000://scrum-users:scrum-users@localhost/scrum-users'
    SECRET_KEY = '123456790'

    DEBUG = True

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql+pg8000://scrum-users:scrum-users@localhost/scrum-users'
    DEBUG = True
