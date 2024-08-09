import os
from dotenv import load_dotenv
basedir = os.path.abspath(os.path.dirname(__file__))


load_dotenv(os.path.join(basedir, '.env'))


class Config:
    # ...
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:////mnt/azure/srl_chat.db'

# 'sqlite:///' + os.path.join(basedir, 'srl_chat.db')
# 'sqlite:////mnt/azure/srl_chat.db'
