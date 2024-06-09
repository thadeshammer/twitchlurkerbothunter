import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://user:password@db:3306/mydatabase')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
