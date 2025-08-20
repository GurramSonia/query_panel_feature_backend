from src.util.models import Permission, Group, UserPermission
from sqlalchemy import text
from flask import session

def _get_allowed_from_user_permissions(user_permissions):
    allowed_tables = [perm.table_name for perm in user_permissions]
    allowed_operations = set()
    allowed_databases = [perm.databases_names for perm in user_permissions if perm.databases_names]
    for perm in user_permissions:
        operations = perm.operations.split(',')
        allowed_operations.update(operations)
    return allowed_tables, allowed_operations, allowed_databases

def _get_allowed_from_group_permissions(name):
    from src.controller import db
    query_string = text("""
        SELECT group_name
        FROM groups_names
        WHERE FIND_IN_SET(:username, users) > 0
    """)
    result = db.session.execute(query_string, {"username": name}).fetchone()
    group_name = result[0] if result else None
    user_permission = Permission.query.filter_by(group=group_name).all()
    allowed_tables = [perm.table_name for perm in user_permission]
    allowed_operations = set()
    allowed_databases = [perm.databases_names for perm in user_permission if perm.databases_names]
    for perm in user_permission:
        operations = perm.operations.split(',')
        allowed_operations.update(operations)
    return allowed_tables, allowed_operations, allowed_databases

def _is_create_collection_or_create(query, source):
    if "create_collection" in query.lower() and source == 'mongodb':
        return True
    if "create" in query.lower() and source == 'mysql':
        return True
    return False

def check_query_permission(role, query, source, name, mysql_db_name, mongo_db_name):
    print(name)
    if not query:
        return False
    if _is_create_collection_or_create(query, source):
        return True

    user_permissions = UserPermission.query.filter_by(username=name).all()
    print(role)
    if user_permissions:
        allowed_tables, allowed_operations, allowed_databases = _get_allowed_from_user_permissions(user_permissions)
        print("allowed tables", allowed_tables)
        print("allowed_operations", allowed_operations)
        print("allowed database are", allowed_databases)
    else:
        allowed_tables, allowed_operations, allowed_databases = _get_allowed_from_group_permissions(name)
        print("allowed tables", allowed_tables)
        print("allowed_operations", allowed_operations)
        print("allowed database are", allowed_databases)

    result = get_table_operation(source, query, mysql_db_name, mongo_db_name)
    table_name = result["table_name"]
    operation = result["operation"]
    database_name = result["database_name"]

    print(database_name in allowed_databases)
    return operation in allowed_operations and table_name in allowed_tables and database_name in allowed_databases

def _parse_mysql_operation(query_upper, query_parts):
    if 'DROP' in query_upper:
        return 'DROP', query_parts[query_upper.split().index("DROP") + 2]
    elif 'SELECT' in query_upper and 'FROM' in query_upper:
        return 'SELECT', query_parts[query_upper.split().index("FROM") + 1]
    elif 'DELETE' in query_upper:
        return 'DELETE', query_parts[query_upper.split().index("FROM") + 1]
    elif 'INSERT' in query_upper:
        return 'INSERT', query_parts[query_upper.split().index("INTO") + 1].split('(')[0]
    elif 'UPDATE' in query_upper:
        return 'UPDATE', query_parts[query_upper.split().index("UPDATE") + 1]
    return None, None

def _parse_mongo_operation(query):
    operation = None
    table_name = None
    if ".drop()" in query:
        operation = "drop"
        parts = query.split('.')
        table_name = parts[-2] if len(parts) >= 3 else None
    elif '.' in query and '(' in query:
        parts = query.split('.')
        if len(parts) >= 3:
            table_name = parts[1]
            operation_with_args = parts[2]
            operation = operation_with_args.split('(')[0]
    elif '.' in query and '(' in query and 'find' in query:
        parts = query.split('.')
        if len(parts) >= 2:
            table_name = parts[1].split('(')[0]
            operation = parts[-1].split('(')[0]
    return operation, table_name

def get_table_operation(source, query, mysql_db_name, mongo_db_name):
    if source == "mysql":
        query_upper = query.upper()
        query_parts = query.split()
        database_name = mysql_db_name
        operation, table_name = _parse_mysql_operation(query_upper, query_parts)
        print("database_name is", database_name)
        print("Operation:", operation, "Table:", table_name)
        return {"table_name": table_name, "operation": operation, "database_name": database_name}
    elif source == 'mongodb':
        database_name = mongo_db_name
        operation, table_name = _parse_mongo_operation(query)
        print("Extracted table_name:", table_name)
        print("Extracted operation:", operation)
        print("Extracted database_name:", database_name)
        return {"table_name": table_name, "operation": operation, "database_name": database_name}
    else:
        return False