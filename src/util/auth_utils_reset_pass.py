from src.util.models import MongoUser,User
from datetime import datetime,timezone
import secrets
from datetime import datetime, timedelta
import mysql.connector
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from settings import MYSQL_USER,MYSQL_DATABASE,MYSQL_HOST,MYSQL_PASSWORD,MYSQL_PORT,MONGO_USERNAME,MONGO_PASSWORD,MONGO_DATABASE,MONGO_HOST,MONGO_PORT
from settings import db_config_service,db_config_local

def check_user_existence_by_email(email):
    from src.controller import db,mongo
    user_sql = db.session.query(User).filter_by(email=email).first()
    print(user_sql)
    user_mongo = mongo.db.users.find_one({"email": email})
    print(user_mongo)
    if  user_sql:
        return user_sql
    elif user_mongo :
        return MongoUser(user_mongo["_id"], user_mongo["username"], user_mongo["email"],user_mongo["password"], user_mongo["role"])
    else:
        return None

def generate_reset_token(email):
    from src.util.models import PasswordResetToken, User,MongoUser
    from src.controller import db,mongo
     # Generate a unique reset token
    token = secrets.token_urlsafe(64)

    # Find the user (could be MySQL or MongoDB)
    user = check_user_existence_by_email(email)
    if not user:
        return None  # Shouldn't happen, since we already check in the route

    # Save the reset token to the database with the user ID
    reset_token = PasswordResetToken(
        token=token,
        user_id=user.id,
        created_at=datetime.now(tz=timezone.utc)
        
    )
    db.session.add(reset_token)
    db.session.commit()
    return token 

def get_user_by_token(token):
    from src.util.models import PasswordResetToken, User
    """
    Get user by the reset token.
    If the token is valid and not expired, return the user object.
    """
    # Look for the reset token in the PasswordResetToken table
    reset_token_entry = PasswordResetToken.query.filter_by(token=token).first()
    
    if not reset_token_entry:
        return None  # Token not found
    
    # Check if the token is expired (e.g., expire after 1 hour)
    token_age = datetime.now(tz=timezone.utc) - reset_token_entry.created_at
    if token_age > timedelta(hours=1):  # 1 hour expiration for example
        return None  # Token is expired
    
    # Return the associated user
    user = User.query.get(reset_token_entry.user_id)
    if user:
        return user
    
    return None  # User not found
mongo_user='ramya'
def update_mysql_password(user_sql, hashed_password, password):
    from src.controller import db
    import mysql.connector
    from settings import MYSQL_HOST, db_config_local, db_config_service

    user_sql.password = hashed_password
    user_sql.originalpass = password
    db.session.commit()
    try:
        if MYSQL_HOST == 'localhost':
            connection = mysql.connector.connect(**db_config_local)
        else:
            connection = mysql.connector.connect(**db_config_service)
        cursor = connection.cursor()
        alter_query = f"ALTER USER '{user_sql.username}'@'%' IDENTIFIED BY '{password}';"
        cursor.execute(alter_query)
        connection.commit()
        cursor.execute("FLUSH PRIVILEGES;")
        print(f"Password updated successfully for MySQL user '{user_sql.username}'.")
    except mysql.connector.Error as err:
        return {"error": f"MySQL error: {err}"}, 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
    return None

def update_mongo_password(mongo, user_mongo, hashed_password, password):
    from settings import MONGO_HOST, MONGO_PASSWORD
    from pymongo import MongoClient

    mongo.db.users.update_one({"_id": user_mongo["_id"]}, {"$set": {"password": hashed_password, "original_pass": password}})
    try:
        if MONGO_HOST == 'localhost':
            client = MongoClient(f"mongodb://ramya:{MONGO_PASSWORD}@localhost:27017/admin")
        else:
            client = MongoClient(f"mongodb://ramya:{MONGO_PASSWORD}@mongo-service:27017/admin")
        db = client.admin
        mongo_username = user_mongo["username"]
        if not isinstance(mongo_username, str):
            raise ValueError("MongoDB username must be a string")
        existing_users = db.command("usersInfo", mongo_username)
        if not existing_users.get("users"):
            print(f"User '{mongo_username}' not found in MongoDB.")
        else:
            db.command("updateUser", mongo_username, pwd=password)
            print(f"Password updated successfully for MongoDB user '{mongo_username}'")
    except Exception as e:
        print(f"Error updating password: {e}")
        return {"error": f"MongoDB error: {str(e)}"}, 500
    finally:
        if 'client' in locals():
            client.close()
    return None

def reset_user_password(user_id, hashed_password, mongo_username, password):
    from src.util.models import User
    from src.controller import db, mongo

    user_sql = User.query.get(user_id)
    user_mongo = mongo.db.users.find_one({"username": mongo_username})
    if user_sql is None and user_mongo is None:
        return {"error": "User not found in both MySQL and MongoDB"}, 404

    mysql_error = None
    mongo_error = None

    if user_sql:
        mysql_error = update_mysql_password(user_sql, hashed_password, password)
        if mysql_error:
            return mysql_error

    if user_mongo:
        mongo_error = update_mongo_password(mongo, user_mongo, hashed_password, password)
        if mongo_error:
            return mongo_error

    return {"message": "Password updated successfully in both MySQL and MongoDB"}, 200