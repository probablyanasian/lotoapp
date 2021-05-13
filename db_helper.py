import os
import sys
import sqlite3
import typing
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
    tables = ['sites', 'assets', 'users', 'tokens', 'sites_users_join', 'incidents', 'users_incidents_join',
        'sources', 'sources_assets_join', 'users_incidents_sources_join', 'incidents_assets_join', 'files']
    for table in tables:
        cursor.execute(f'DROP TABLE IF EXISTS {table};')
    # cursor.execute('DROP TABLE IF EXISTS sites;')
    # cursor.execute('DROP TABLE IF EXISTS assets;')
    # cursor.execute('DROP TABLE IF EXISTS users;')
    # cursor.execute('DROP TABLE IF EXISTS tokens;')
    # cursor.execute('DROP TABLE IF EXISTS sites_users_join;')
    # cursor.execute('DROP TABLE IF EXISTS incidents;')
    # cursor.execute('DROP TABLE IF EXISTS users_incidents_join;')
    # cursor.execute('DROP TABLE IF EXISTS sources;')
    # cursor.execute('DROP TABLE IF EXISTS sources_assets_join;')
    # cursor.execute('DROP TABLE IF EXISTS users_sources_join;')
    # cursor.execute('DROP TABLE IF EXISTS incidents_assets_join;')
    # cursor.execute('DROP TABLE IF EXISTS files;')

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sites (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        location TEXT NOT NULL,
        archived INTEGER NOT NULL,
        key TEXT NOT NULL
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        fname TEXT NOT NULL,
        lname TEXT NOT NULL,
        uname TEXT NOT NULL UNIQUE,
        phone TEXT NOT NULL,
        email TEXT,
        share_contact INTEGER NOT NULL,
        archived INTEGER NOT NULL,
        pass TEXT NOT NULL
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT NOT NULL,
        creation_time INTEGER NOT NULL,
        user_id TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sites_users_join (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        is_manager INTEGER NOT NULL,
        user_id TEXT NOT NULL,
        site_id TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (site_id) REFERENCES sites(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
        id TEXT PRIMARY KEY,
        key TEXT NOT NULL,
        creator_id TEXT NOT NULL,
        site_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        l_date INTEGER NOT NULL,
        resolved INTEGER NOT NULL,
        ul_date INTEGER,
        FOREIGN KEY (site_id) REFERENCES sites(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_incidents_join (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        incident_id TEXT NOT NULL,
        leader INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (incident_id) REFERENCES incidents(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
        id TEXT PRIMARY KEY,
        fpath TEXT NOT NULL,
        user_id TEXT NOT NULL,
        site_id TEXT NOT NULL,
        incident_id TEXT NOT NULL,
        source_id TEXT NOT NULL,
        time INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (site_id) REFERENCES sites(id),
        FOREIGN KEY (incident_id) REFERENCES incidents(id),
        FOREIGN KEY (source_id) REFERENCES sources(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
        id TEXT PRIMARY KEY,
        key TEXT NOT NULL,
        creator_id TEXT NOT NULL,
        site_id TEXT NOT NULL,
        name TEXT NOT NULL,
        location TEXT NOT NULL,
        archived INTEGER NOT NULL,
        manufacturer TEXT NOT NULL, 
        model_number TEXT NOT NULL,
        serial_number TEXT NOT NULL,
        shutoff_instructions TEXT NOT NULL,
        startup_instructions TEXT NOT NULL,
        creation_time INTEGER NOT NULL,
        last_updated_time INTEGER NOT NULL,
        FOREIGN KEY (site_id) REFERENCES sites(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sources (
        id TEXT PRIMARY KEY,
        site_id TEXT NOT NULL,
        creator_id TEXT NOT NULL,
        name TEXT NOT NULL,
        location TEXT NOT NULL,
        type TEXT NOT NULL,
        magnitude TEXT,
        locked INTEGER NOT NULL,
        archived INTEGER NOT NULL,
        shutoff_instructions TEXT NOT NULL,
        startup_instructions TEXT NOT NULL,
        verification_instructions TEXT NOT NULL,
        FOREIGN KEY (site_id) REFERENCES sites(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_incidents_sources_join (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        incident_id TEXT NOT NULL,
        source_id TEXT NOT NULL,
        locked INTEGER NOT NULL,
        was_locked INTEGER NOT NULL,
        initial_lock_time INTEGER,
        final_unlock_time INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (incident_id) REFERENCES incidents(id),
        FOREIGN KEY (source_id) REFERENCES sources(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sources_assets_join (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id TEXT NOT NULL,
        source_id TEXT NOT NULL,
        FOREIGN KEY (asset_id) REFERENCES assets(id),
        FOREIGN KEY (source_id) REFERENCES sources(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents_assets_join (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT NOT NULL,
        asset_id TEXT NOT NULL,
        FOREIGN KEY (incident_id) REFERENCES incidents(id),
        FOREIGN KEY (asset_id) REFERENCES assets(id)
        );
    """)

    for table in tables:
        cursor.execute(f'DROP TABLE IF EXISTS {table}_deleted;')
        cursor.execute(f'CREATE TABLE {table}_deleted AS SELECT * FROM {table};')
        cursor.execute(f'ALTER TABLE {table}_deleted ADD COLUMN deletion_time INTEGER;')
        cursor.execute(f'ALTER TABLE {table}_deleted ADD COLUMN deletion_user_id TEXT;')

    conn.commit()


if __name__ == '__main__':
    setup_db()
