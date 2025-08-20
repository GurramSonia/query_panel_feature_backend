import os
FLASK_DEBUG = os.environ.get('FLASK_DEBUG', True)
MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD','fkoh xfak aizr dkwo')
my_email=os.environ.get('my_email','flask772@gmail.com')
BaseURL=os.environ.get('BaseURL','http://localhost:3000/query-ui')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'Ramya772819390')  # Default password for MySQL user
MYSQL_HOST = os.getenv('MYSQL_HOST','localhost')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
MONGO_USERNAME = os.getenv('MONGO_INITDB_ROOT_USERNAME')
MONGO_PASSWORD = os.getenv('MONGO_INITDB_ROOT_PASSWORD')
MONGO_HOST = os.getenv('MONGO_HOST','localhost')
MONGO_PORT = os.getenv('MONGO_PORT', '27017')
MONGO_DATABASE = os.getenv('MONGO_DATABASE')
MONGO_PASSWORD=os.getenv('MONGO_PASSWORD','Ramya772' )  
MYSQL_LOCAL_PASS=os.getenv('MYSQL_LOCAL_PASS','Sonia@77281')
TEST_PASSWORD = os.getenv('TEST_PASSWORD', 'testpass123')  # Default password for testing
DEFAULT_MAIL = os.getenv('DEFAULT_MAIL', 'username@gmail.com')
MYSQL_LOCAL_USER_PASS = os.getenv('MYSQL_LOCAL_USER_PASS','Ramya772819390')  # Default password for local MySQL user





db_config_service= {
    "host": MYSQL_HOST,
    "user": MYSQL_USER,  # Change to your MySQL admin user
    "password":MYSQL_PASSWORD ,  # Change to your MySQL root password
    "database": "querydatabase2"
}

db_config_local= {
    "host": MYSQL_HOST,
    "user": "root",  # Change to your MySQL admin user
    "password": MYSQL_LOCAL_PASS,  # Change to your MySQL root password
    "database": "querydatabase2"
}


# JWT secret for signing tokens
JWT_SECRET = os.environ.get('JWT_SECRET', 'your_jwt_secret')