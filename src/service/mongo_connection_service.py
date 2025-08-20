from datetime import datetime
from pymongo import MongoClient
from src.util.helpers import convert_objectid_and_datetime
from flask import session,flash,get_flashed_messages
from src.util.models import AuditLog,UserPermission,Permission
from sqlalchemy import text

from datetime import datetime, timezone
from pymongo import MongoClient
from src.util.helpers import convert_objectid_and_datetime
from flask import session, flash, get_flashed_messages
from src.util.models import AuditLog, UserPermission, Permission
from sqlalchemy import text

def _extract_collection_name(query):
    if '.' in query and '(' in query and 'find' in query:
        parts = query.split('.')
        return parts[1].split('(')[0]
    elif ".drop()" in query:
        parts = query.split('.')
        return parts[-2] if len(parts) >= 3 else None
    elif '.' in query and '(' in query:
        parts = query.split('.')
        return parts[1]
    return None

def _get_user_permission(dbs, username):
    user_permission = dbs.session.query(UserPermission).filter_by(username=username).first()
    if not user_permission:
        query_string = text("""
            SELECT group_name
            FROM groups_names
            WHERE FIND_IN_SET(:username, users) > 0
        """)
        result = dbs.session.execute(query_string, {"username": username}).fetchone()
        group_name = result[0] if result else None
        user_permission = dbs.session.query(Permission).filter_by(group=group_name).first()
    return user_permission

def _filter_results(results, can_view_email, can_view_pass):
    for row in results:
        if not can_view_email and 'email' in row:
            del row['email']
        if not can_view_pass and 'password' in row:
            del row['password']
        if 'original_pass' in row:
            del row['original_pass']
    return results

def _log_audit(dbs, mongo, username, action, db_name, connection_uris, timestamp):
    log = AuditLog(username=username, action=action, database_name=db_name, connection_string=connection_uris)
    dbs.session.add(log)
    dbs.session.commit()
    mongo.db.audit_logs.insert_one({
        "username": username,
        "query": action,
        "database_name": db_name,
        "timestamp": timestamp,
    })

def execute_mongo_query(query, connection_uri, connection_uris):
    """Execute MongoDB queries (find & DML operations)."""
    client = MongoClient(connection_uri)
    db = client.get_database()
    db_name = connection_uri.split("/")[-1].split("?")[0]
    collection_names = db.list_collection_names()
    print("collection_nmaes", collection_names)
    username = session.get('user_name', 'Unknown User')
    role = session.get('role')
    print("user role in mongo is", role)
    timestamp = datetime.now(timezone.utc)
    results = None
    flash_messages = None

    collection_name = _extract_collection_name(query)
    if collection_name not in collection_names:
        return {"error": "Collection does not exist"}, 400

    from src.controller import db as dbs, mongo

    if 'find' in query:
        result = eval(query)
        results = convert_objectid_and_datetime(list(result))
        print("final mongo results are", list(results))

        user_permission = _get_user_permission(dbs, username)
        if user_permission is None:
            print(f"No permissions found for user: {username}")
            can_view_email = False
            can_view_pass = False
        else:
            can_view_email = user_permission.view_email
            can_view_pass = user_permission.view_pass

        print("Can View Password:", can_view_pass)
        print("Can View Email:", can_view_email)
        print("Username:", username)
        results = _filter_results(results, can_view_email, can_view_pass)

    elif any(op in query for op in ["insert_one", "insert_many", "update_one", "update_many", "delete_one", "delete_many", "drop", 'create_collection']):
        print("enterd into mongo execute")
        eval(query)
        results = []
        flash(f"MongoDB {query.split('(')[0]} query executed successfully")
    else:
        print("unexpected error")
        return {"error": "Invalid mongodb queryFormat"}

    action = f"{query}"
    print("action is", action)
    print(db_name, "is database")
    print("DB Session Type:", type(dbs.session))
    _log_audit(dbs, mongo, username, action, db_name, connection_uris, timestamp)
    flash_messages = get_flashed_messages()
    return {"results": results, "flash_messages": flash_messages}