import os

class Config(object):
    DEBUG = False
    LOGGING_PATH = os.getenv('LOGGING_PATH', 'python_logging/logging.yaml')

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
    SECRET_KEY = os.environ['SECRET_KEY']
    SALT = os.environ['SALT']
    SCRUM_API = os.environ['SCRUM_API']
    DEBUG = True

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
    SECRET_KEY = os.environ['SECRET_KEY']
    SALT = os.environ['SALT']
    SCRUM_API = os.environ['SCRUM_API']

    DEBUG = True
