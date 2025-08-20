from flask import Blueprint,url_for,Flask
import os
from flask_mail import Mail
from flask_restx import Api,apidoc
from src.controller.auth.auth_controller_auth import auth_ns_auth
from src.controller.auth.auth_controller_reset_pass import auth_ns_reset_pass
from src.controller.admin.admin_get_controller import admin_ns_get 
from src.controller.admin.admin_add_controller import admin_ns_add
from src.controller.admin.admin_remove_controller import admin_ns_remove
from src.controller.query_connection_controller import connection_ns
from src.util.models import db, mongo
from settings import MYSQL_USER,MYSQL_DATABASE,MYSQL_HOST,MYSQL_PASSWORD,MYSQL_PORT,MONGO_USERNAME,MONGO_PASSWORD,MONGO_DATABASE,MONGO_HOST,MONGO_PORT,MYSQL_LOCAL_USER_PASS  

mail = Mail()
class MyCustomApi(Api):
    def _register_apidoc(self, app: Flask) -> None:
        conf = app.extensions.setdefault('restx', {})  # Use 'restx' instead of 'restplus'
        custom_apidoc = apidoc.Apidoc('restx_doc', 'flask_restx.apidoc',  # Use 'flask_restx' instead of 'flask_restplus'
                                      template_folder='templates', static_folder='static',
                                      static_url_path='/queryapi')

        @custom_apidoc.add_app_template_global
        def swagger_static(filename: str) -> str:
            return url_for('restx_doc.static', filename=filename)  # Use 'restx_doc' instead of 'restplus_doc'

        if not conf.get('apidoc_registered', False):
            app.register_blueprint(custom_apidoc)
            conf['apidoc_registered'] = True

queryapi= Blueprint('my_blueprint', __name__, url_prefix='/queryapi')
API = MyCustomApi(queryapi, version='1.0', title='QueryPanel API', description='API Querypanel',
                  validate=True) 
 
ADMIN_PATH = '/admin'
AUTH_PATH = '/auth'
def init_app(app):
    MYSQL_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
        if MYSQL_USER and MYSQL_PASSWORD and MYSQL_HOST and MYSQL_DATABASE
        else f"mysql+pymysql://GurramSonia:{MYSQL_LOCAL_USER_PASS}@localhost/querydatabase2"
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = MYSQL_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # MongoDB configuration
    MONGO_URI = (
        f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}"
        if MONGO_USERNAME and MONGO_PASSWORD and MONGO_HOST and MONGO_DATABASE
        else 'mongodb://localhost:27017/mongo-database'
    )
    app.config['MONGO_URI'] = MONGO_URI
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    from settings import JWT_SECRET
    app.config['JWT_SECRET'] = JWT_SECRET

    db.init_app(app)
    mongo.init_app(app)
    mail.init_app(app)
   

    # Register namespaces with the API
    API.add_namespace(auth_ns_auth, path=AUTH_PATH)
    API.add_namespace(auth_ns_reset_pass, path=AUTH_PATH)
    API.add_namespace(admin_ns_add, path=ADMIN_PATH )
    API.add_namespace(admin_ns_get, path=ADMIN_PATH )
    API.add_namespace(admin_ns_remove, path=ADMIN_PATH )
    API.add_namespace(connection_ns, path='/connection/')

    # Register the Blueprint with the app
    app.register_blueprint(queryapi)

    # Create database tables
    with app.app_context():
        db.create_all()
