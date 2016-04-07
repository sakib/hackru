import os

basedir = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = 'hackru'

SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite'

OAUTH_CREDENTIALS = {
    'mlh': {
        'id': '95bec811ea77fc70aa8e920327ea02cef624b2e47851c71a4f559551d54a6c65',
        'secret': '30ce1c3a4d5314efe56537f5d0a4275caf1809efb12866b646f2225e476169de'
    }
}

UPLOAD_FOLDER = os.path.join(basedir, 'hackru/resumes')

LOG_FILENAME = os.path.join(basedir, 'hackru.log')

LOG_FORMAT = "%(levelname)s %(asctime)s --> %(message)s [in %(filename)s:%(lineno)d]"

ALLOWED_EXTENSIONS = ['txt', 'pdf', 'doc', 'docx']

MAX_CONTENT_LENGTH = 2 * 1024 * 1024 # 2 MB max

WAVE_LIMIT = 1000

MAIL_SERVER = 'smtp.gmail.com'

MAIL_PORT = 587

MAIL_USE_TLS = True

MAIL_USE_SSL = False

MAIL_USERNAME = 'team@hackru.org'

MAIL_PASSWORD = 'sesh112@ruTEAM'
