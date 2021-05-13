CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE sites (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        location TEXT NOT NULL,
        archived INTEGER NOT NULL,
        key TEXT NOT NULL
        );
CREATE TABLE users (
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
CREATE TABLE tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT NOT NULL,
        creation_time INTEGER NOT NULL,
        user_id TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
        );
CREATE TABLE sites_users_join (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        is_manager INTEGER NOT NULL,
        user_id TEXT NOT NULL,
        site_id TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (site_id) REFERENCES sites(id)
        );
CREATE TABLE incidents (
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
CREATE TABLE users_incidents_join (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        incident_id TEXT NOT NULL,
        leader INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (incident_id) REFERENCES incidents(id)
        );
CREATE TABLE files (
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
CREATE TABLE assets (
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
        verification_instructions TEXT NOT NULL,
        FOREIGN KEY (site_id) REFERENCES sites(id)
        );
CREATE TABLE sources (
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
        creation_time INTEGER NOT NULL,
        last_updated_time INTEGER NOT NULL,
        FOREIGN KEY (site_id) REFERENCES sites(id)
        );
CREATE TABLE users_incidents_sources_join (
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
CREATE TABLE sources_assets_join (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id TEXT NOT NULL,
        source_id TEXT NOT NULL,
        FOREIGN KEY (asset_id) REFERENCES assets(id),
        FOREIGN KEY (source_id) REFERENCES sources(id)
        );
CREATE TABLE incidents_assets_join (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT NOT NULL,
        asset_id TEXT NOT NULL,
        FOREIGN KEY (incident_id) REFERENCES incidents(id),
        FOREIGN KEY (asset_id) REFERENCES assets(id)
        );
CREATE TABLE sites_deleted(
  id TEXT,
  name TEXT,
  location TEXT,
  archived INT,
  "key" TEXT
, deletion_time INTEGER, deletion_user_id TEXT);
CREATE TABLE assets_deleted(
  id TEXT,
  "key" TEXT,
  creator_id TEXT,
  site_id TEXT,
  name TEXT,
  location TEXT,
  archived INT,
  manufacturer TEXT,
  model_number TEXT,
  serial_number TEXT,
  shutoff_instructions TEXT,
  startup_instructions TEXT,
  creation_time INT,
  last_updated_time INT,
  verification_instructions TEXT
, deletion_time INTEGER, deletion_user_id TEXT);
CREATE TABLE users_deleted(
  id TEXT,
  fname TEXT,
  lname TEXT,
  uname TEXT,
  phone TEXT,
  email TEXT,
  share_contact INT,
  archived INT,
  pass TEXT
, deletion_time INTEGER, deletion_user_id TEXT);
CREATE TABLE tokens_deleted(
  id INT,
  token TEXT,
  creation_time INT,
  user_id TEXT
, deletion_time INTEGER, deletion_user_id TEXT);
CREATE TABLE sites_users_join_deleted(
  id INT,
  is_manager INT,
  user_id TEXT,
  site_id TEXT
, deletion_time INTEGER, deletion_user_id TEXT);
CREATE TABLE incidents_deleted(
  id TEXT,
  "key" TEXT,
  creator_id TEXT,
  site_id TEXT,
  reason TEXT,
  l_date INT,
  resolved INT,
  ul_date INT
, deletion_time INTEGER, deletion_user_id TEXT);
CREATE TABLE users_incidents_join_deleted(
  id INT,
  user_id TEXT,
  incident_id TEXT,
  leader INT
, deletion_time INTEGER, deletion_user_id TEXT);
CREATE TABLE sources_deleted(
  id TEXT,
  site_id TEXT,
  creator_id TEXT,
  name TEXT,
  location TEXT,
  type TEXT,
  magnitude TEXT,
  locked INT,
  archived INT,
  shutoff_instructions TEXT,
  startup_instructions TEXT,
  verification_instructions TEXT,
  creation_time INT,
  last_updated_time INT
, deletion_time INTEGER, deletion_user_id TEXT);
CREATE TABLE sources_assets_join_deleted(
  id INT,
  asset_id TEXT,
  source_id TEXT
, deletion_time INTEGER, deletion_user_id TEXT);
CREATE TABLE users_incidents_sources_join_deleted(
  id INT,
  user_id TEXT,
  incident_id TEXT,
  source_id TEXT,
  locked INT,
  was_locked INT,
  initial_lock_time INT,
  final_unlock_time INT
, deletion_time INTEGER, deletion_user_id TEXT);
CREATE TABLE incidents_assets_join_deleted(
  id INT,
  incident_id TEXT,
  asset_id TEXT
, deletion_time INTEGER, deletion_user_id TEXT);
CREATE TABLE files_deleted(
  id TEXT,
  fpath TEXT,
  user_id TEXT,
  site_id TEXT,
  incident_id TEXT,
  source_id TEXT,
  time INT
, deletion_time INTEGER, deletion_user_id TEXT);
