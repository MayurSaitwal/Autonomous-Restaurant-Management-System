import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'restaurant_secret_key_2024')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'mysql-service')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', os.environ.get('password', 'password'))
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'restaurant_db')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))

    STAFF_USERNAME = 'staff'
    STAFF_PASSWORD = 'admin123'
