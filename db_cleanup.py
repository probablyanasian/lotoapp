import os
import sys
import time
import sqlite3
from sqlite3 import Error
from sqlite3.dbapi2 import Connection, Cursor

conn = None
cursor = None

def create_connection() -> Connection:
    conn_loc = None
    try:
        print(sys.version)
        print(os.path.join(sys.argv[0], 'sqlite.db'))
        conn_loc = sqlite3.connect('sqlite.db', check_same_thread=False)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        if conn_loc:
            return conn_loc

conn = create_connection()
cursor = conn.cursor()

def execute(query, args: dict) -> None:
    cursor.execute(query, args)
    conn.commit()

def fetch(query, args: dict) -> list:
    cursor.execute(query, args)
    fetched = cursor.fetchall()
    print(fetched) # debug purposes only:tm:
    return fetched

def close_connection() -> None:
    conn.close()

def setup_db() -> None:
    execute('INSERT INTO tokens_deleted (token, creation_time, user_id, deletion_time, deletion_user_id)' +
        f'SELECT token, creation_time, user_id, :time, :sys_uid FROM tokens WHERE creation_time < {int(time.time()) - 24*60*60};',
        {'time': int(time.time()), 'sys_uid': 'SYSTEM_CLEANUP'})
    execute(f'DELETE FROM tokens WHERE creation_time < {int(time.time()) - 24*60*60};', {})

if __name__ == '__main__':
    setup_db()
