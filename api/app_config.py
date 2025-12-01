import os
from dotenv import load_dotenv
basedir = os.path.abspath(os.path.dirname(__file__))


load_dotenv(os.path.join(basedir, '.env'))


class Config:
    PG_HOST = os.environ.get("PG_HOST")
    PG_PORT = os.environ.get("PG_PORT")
    PG_USER = os.environ.get("PG_USER")
    PG_PASSWORD = os.environ.get("PG_PASSWORD")
    PG_DB = os.environ.get("PG_DB")
    DB_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    SQLALCHEMY_DATABASE_URI = DB_URL



#print(os.environ)
print(f"postgresql://{Config.PG_USER}:{Config.PG_PASSWORD}@{Config.PG_HOST}:{Config.PG_PORT}/{Config.PG_DB}")

# 'sqlite:///' + os.path.join(basedir, 'srl_chat.db')
# 'sqlite:////mnt/azure/srl_chat.db'
# DATABASE_URL=postgresql://postgres:chat@postgres:5432/srl_chat
