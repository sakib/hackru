import os

basedir = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = 'hackru'

SQLALCHEMY_DATABASE_URI = 'sqlite:///../db.sqlite'

OAUTH_CREDENTIALS = {
    'mlh': {
        'id': '95bec811ea77fc70aa8e920327ea02cef624b2e47851c71a4f559551d54a6c65',
        'secret': '30ce1c3a4d5314efe56537f5d0a4275caf1809efb12866b646f2225e476169de'
    }
}

UPLOAD_FOLDER = os.path.join(basedir, 'resumes')

ALLOWED_EXTENSIONS = ['txt', 'pdf', 'doc', 'docx']
