import mysql.connector
from urllib.parse import urlparse
from datetime import datetime
from src.util.helpers import convert_objectid_and_datetime
from flask import session, flash, get_flashed_messages
from src.util.models import AuditLog, UserPermission, Permission
from sqlalchemy import text


def get_mysql_connection(uri):
    """Connect to MySQL using a URI."""
    print("entered into mysql_connection uri")
    print("Enterd into mysql_connection_uri")
    print("uri is the ", uri)
    uris = f"mysql+pymysql://{uri}"
    print(uris)
    parsed_uri = urlparse(uri)
    print("parse uri", parsed_uri)
    database_name = parsed_uri.path.lstrip('/')
    print("database_name is", database_name)
    conn = mysql.connector.connect(
        host=parsed_uri.hostname,
        user=parsed_uri.username,
        password=parsed_uri.password,
        database=parsed_uri.path.lstrip('/'),
        port=parsed_uri.port or 3306
    )
    return conn, database_name

def filter_result_columns(result_dict, can_view_email, can_view_pass):
    for row in result_dict:
        if not can_view_email and 'email' in row:
            del row['email']
        if not can_view_pass and 'password' in row:
            del row['password']
        for sensitive in ['connection_string', 'originalpass']:
            if sensitive in row:
                del row[sensitive]
    return result_dict

def get_user_permission(db, user_permission_model, permission_model, username, source_type, database_name, table_name):
    user_permission = db.session.query(user_permission_model).filter_by(
        username=username, source=source_type, databases_names=database_name, table_name=table_name
    ).first()
    if not user_permission:
        from src.controller import mongo
        query_string = text("""
            SELECT group_name
            FROM groups_names
            WHERE FIND_IN_SET(:username, users) > 0
        """)
        result = db.session.execute(query_string, {"username": username}).fetchone()
        group_name = result[0] if result else None
        user_permission = db.session.query(permission_model).filter_by(
            group=group_name, source=source_type, databases_names=database_name, table_name=table_name
        ).first()
    return user_permission

def handle_select_query(cursor, query, name, source_type, mysql_db_name, mongo_db_name, db, user_permission_model, permission_model):
    cursor.execute(query)
    column_names = [desc[0] for desc in cursor.description]
    result = cursor.fetchall()
    formatted_results = [
        tuple(item.strftime('%Y-%m-%d %H:%M:%S') if isinstance(item, datetime) else item for item in row)
        for row in result
    ]
    result_dict = [dict(zip(column_names, row)) for row in formatted_results]
    from src.util.role_connection_permissions import get_table_operation
    result_table = get_table_operation(source_type, query, mysql_db_name, mongo_db_name)
    table_name = result_table["table_name"]
    database_name = result_table["database_name"]
    user_permission = get_user_permission(db, user_permission_model, permission_model, name, source_type, database_name, table_name)
    can_view_email = user_permission.view_email if user_permission else False
    can_view_pass = user_permission.view_pass if user_permission else False
    result_dict = filter_result_columns(result_dict, can_view_email, can_view_pass)
    return result_dict

def handle_dml_query(cursor, conn, query):
    cursor.execute(query)
    conn.commit()
    flash(f"Mysql {query.split('(')[0]} query executed successfully")
    return []

def execute_mysql_query(query, connection_uri, connection_uris, source_type, mysql_db_name, mongo_db_name):
    """Execute MySQL queries (SELECT & DML operations)."""
    conn, db_name = get_mysql_connection(connection_uri)
    cursor = conn.cursor()
    name = session.get('user_name')
    result_dict = []
    flash_messages = None

    try:
        from src.controller import db
        from src.util.models import UserPermission, Permission, AuditLog

        if 'select' in query.lower() and 'from' in query.lower():
            result_dict = handle_select_query(
                cursor, query, name, source_type, mysql_db_name, mongo_db_name, db, UserPermission, Permission
            )
        elif any(op in query.upper() for op in ['INSERT', 'CREATE TABLE', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'USE']):
            result_dict = handle_dml_query(cursor, conn, query)
        else:
            return {"error": "Invalid mysql query Format"}

        action = f"{query}"
        log = AuditLog(username=name, action=action, database_name=db_name, connection_string=connection_uris)
        db.session.add(log)
        db.session.commit()
        flash_messages = get_flashed_messages()
        return {"results": result_dict, "flash_messages": flash_messages}

    except Exception as e:
        print("error in executing the mysql commands", str(e))
        return {"error": str(e)}

    finally:
         cursor.close()
         conn.close()