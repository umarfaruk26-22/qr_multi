import mysql.connector
from mysql.connector import Error, pooling
from contextlib import contextmanager
from config import Config
import logging

logger = logging.getLogger(__name__)

_connection_pool = None

def get_connection_pool():
    """Get or create MySQL connection pool."""
    global _connection_pool
    if _connection_pool is None:
        try:
            _connection_pool = pooling.MySQLConnectionPool(
                pool_name="employee_qr_pool",
                pool_size=10,
                pool_reset_session=True,
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci",
                autocommit=False
            )
            logger.info("MySQL Connection Pool initialized successfully.")
        except Error as e:
            logger.error(f"Error initializing MySQL Connection Pool: {e}")
            _connection_pool = None
    return _connection_pool


def get_db_connection(database=None):
    """
    Get a direct connection to MySQL.
    Useful for init_db operations or when pool is not available.
    """
    db_name = database if database is not None else Config.DB_NAME
    conn_params = {
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci',
        'autocommit': False
    }
    if db_name:
        conn_params['database'] = db_name
        
    return mysql.connector.connect(**conn_params)


@contextmanager
def get_db_cursor(commit=False, dictionary=True):
    """
    Context manager for database cursor.
    Acquires a connection from pool or direct connection, yields cursor,
    handles auto-commit/rollback, and ensures proper cleanup.
    """
    conn = None
    pool = get_connection_pool()
    try:
        if pool:
            conn = pool.get_connection()
        else:
            conn = get_db_connection()
            
        cursor = conn.cursor(dictionary=dictionary)
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error during transaction: {e}")
            raise e
        finally:
            cursor.close()
    finally:
        if conn and conn.is_connected():
            conn.close()


def query_db(query, params=(), one=False, commit=False):
    """
    Helper function to execute a parameterized query.
    Returns:
        - List of dicts (if one=False and not commit)
        - Single dict (if one=True and not commit)
        - Last inserted id / row count if commit=True
    """
    with get_db_cursor(commit=commit, dictionary=True) as cursor:
        cursor.execute(query, params)
        if commit:
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
        rv = cursor.fetchall()
        return (rv[0] if rv else None) if one else rv
