from flask import Flask, request
import os
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(os.environ.get('SETTINGS'))


# Create dummy secrey key so we can use sessions



# Create database connection object
db = SQLAlchemy(app)
