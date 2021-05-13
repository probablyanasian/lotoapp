import Incident
import Source
import time
import db_helper
import custom_utils

class Site:
    def __init__(self, i_name: str, i_manager: str, i_location: str) -> None:
        self.id = custom_utils.random_id(32)
        self.key = custom_utils.random_id(32)

        db_helper.execute('INSERT INTO sites (id, key, name, location, archived) VALUES (:id, :key, :name, :location, :archived);', 
        {'id': self.id, 'name': i_name, 'key': self.key, 'location': i_location, 'archived': 0})
        db_helper.execute('INSERT INTO sites_users_join (is_manager, user_id, site_id) VALUES (:is_manager, :user_id, :site_id);', 
        {'is_manager': 1, 'user_id': i_manager, 'site_id': self.id})

def check_id_exists(i_site_id: str) -> bool:
    res = db_helper.fetch('SELECT * FROM sites WHERE id = :site_id;', {'site_id': i_site_id})
    if len(res) != 0:
        return True
    return False

def delete_site(i_site_id: str, i_user_id: str) -> None:
    if check_id_exists(i_site_id):
        incidents_tup_list = Incident.get_incidents_from_site(i_site_id)
        for incident_tup in incidents_tup_list:
            db_helper.execute('INSERT INTO users_incidents_join_deleted (user_id, incident_id, resolved, deletion_time, deletion_user_id)' +
            f'SELECT user_id, :incident_id, resolved, :time, :del_uid FROM users_incidents_join WHERE incident_id = :incident_id;',
            {'time': int(time.time()), 'del_uid': i_user_id, 'incident_id': incident_tup[0]})
            db_helper.execute('DELETE FROM users_incidents_join WHERE incident_id = :incident_id;', {'incident_id': incident_tup[0]})
            db_helper.execute('INSERT INTO incidents_assets_join_deleted (incident_id, asset_id, deletion_time, deletion_user_id)' +
            f'SELECT :incident_id, asset_id, :time, :del_uid FROM incidents_assets_join WHERE incident_id = :incident_id;',
            {'time': int(time.time()), 'del_uid': i_user_id, 'incident_id': incident_tup[0]})
            db_helper.execute('DELETE FROM incidents_assets_join WHERE incident_id = :incident_id;', {'incident_id': incident_tup[0]})

        sources_tup_list = Source.get_info_from_site(i_site_id)
        for source_tup in sources_tup_list:
            db_helper.execute('INSERT INTO sources_assets_join_deleted (asset_id, source_id, deletion_time, deletion_user_id)' +
            f'SELECT asset_id, :source_id, :time, :del_uid FROM sources_assets_join WHERE source_id = :source_id;',
            {'time': int(time.time()), 'del_uid': i_user_id, 'source_id': source_tup[0]})
            db_helper.execute('DELETE FROM sources_assets_join WHERE source_id = :source_id;', {'source_id': source_tup[0]})
            db_helper.execute('INSERT INTO users_incidents_sources_join_deleted (user_id, incident_id, source_id, locked, was_locked, deletion_time, deletion_user_id)' +
            f'SELECT user_id, incident_id, :source_id, locked, was_locked, :time, :del_uid FROM users_incidents_sources_join WHERE source_id = :source_id;',
            {'time': int(time.time()), 'del_uid': i_user_id, 'source_id': source_tup[0]})
            db_helper.execute('DELETE FROM users_incidents_sources_join WHERE source_id = :source_id;', {'source_id': source_tup[0]})

        db_helper.execute('INSERT INTO sites_deleted (id, key, name, location, deletion_time, deletion_user_id)' +
        f'SELECT id, key, name, location, :time, :del_uid FROM sites WHERE id = :site_id;',
        {'time': int(time.time()), 'del_uid': i_user_id, 'site_id': i_site_id})
        db_helper.execute('DELETE FROM sites WHERE id = :site_id;', {'site_id': i_site_id})
        db_helper.execute('INSERT INTO sites_users_join_deleted (user_id, site_id, is_manager, deletion_time, deletion_user_id)' +
        f'SELECT user_id, :site_id, is_manager, :time, :del_uid FROM sites_users_join WHERE site_id = :site_id;',
        {'time': int(time.time()), 'del_uid': i_user_id, 'site_id': i_site_id})
        db_helper.execute('DELETE FROM sites_users_join WHERE site_id = :site_id;', {'site_id': i_site_id})
        db_helper.execute('INSERT INTO sources_deleted (id, site_id, creator_id, name, location, type, magnitude, locked, archived, ' +
        'shutoff_instructions, startup_instructions, verification_instructions, deletion_time, deletion_user_id)' +
        f'SELECT id, :site_id, creator_id, name, location, type, magnitude, locked, archived, ' + 
        'shutoff_instructions, startup_instructions, verification_instructions, :time, :del_uid FROM sources WHERE site_id = :site_id;',
        {'time': int(time.time()), 'del_uid': i_user_id, 'site_id': i_site_id})
        db_helper.execute('DELETE FROM sources WHERE site_id = :site_id;', {'site_id': i_site_id})
        db_helper.execute('INSERT INTO assets_deleted (id, key, creator_id, site_id, name, location, archived, '
        + 'manufacturer, model_number, serial_number, shutoff_instructions, startup_instructions, creation_time, last_updated_time, verification_instructions, '
        + 'deletion_time, deletion_user_id)' +
        f'SELECT id, key, creator_id, :site_id, name, location, archived, ' + 
        'manufacturer, model_number, serial_number, shutoff_instructions, startup_instructions, creation_time, last_updated_time, verification_instructions, ' + 
        ':time, :del_uid FROM assets WHERE site_id = :site_id;',
        {'time': int(time.time()), 'del_uid': i_user_id, 'site_id': i_site_id})
        db_helper.execute('DELETE FROM assets WHERE site_id = :site_id;', {'site_id': i_site_id})
        db_helper.execute('INSERT INTO incidents_deleted (id, key, site_id, creator_id, reason, l_date, ul_date, deletion_time, deletion_user_id)' +
        f'SELECT id, key, :site_id, creator_id, reason, l_date, ul_date, :time, :del_uid FROM incidents WHERE site_id = :site_id;',
        {'time': int(time.time()), 'del_uid': i_user_id, 'site_id': i_site_id})
        db_helper.execute('DELETE FROM incidents WHERE site_id = :site_id;', {'site_id': i_site_id})
        db_helper.execute('INSERT INTO files_deleted (id, user_id, site_id, incident_id, source_id, deletion_time, deletion_user_id)' +
        f'SELECT id, user_id, :site_id, incident_id, source_id, :time, :del_uid FROM files WHERE site_id = :site_id;',
        {'time': int(time.time()), 'del_uid': i_user_id, 'site_id': i_site_id})
        db_helper.execute('DELETE FROM files WHERE site_id = :site_id;', {'site_id': i_site_id})


def regenKey(i_id: str) -> None:
    key = custom_utils.random_id(32)
    db_helper.execute("UPDATE sites SET key = :key WHERE id = :id;", {'key': key, 'id': i_id})

def check_key(i_key: str) -> bool:
    res = db_helper.fetch('SELECT * FROM sites WHERE key = :key;', {'key': i_key})
    if len(res) != 0:
        return True
    return False

def get_info_from_id(i_site_id: str) -> str:
    return db_helper.fetch('SELECT name, location FROM sites WHERE id = :site_id;', {'site_id': i_site_id})[0]

def get_key_from_id(i_site_id: str) -> str:
    return db_helper.fetch('SELECT key FROM sites WHERE id = :site_id;', {'site_id': i_site_id})[0][0]

def get_id_from_key(i_site_key: str) -> str:
    return db_helper.fetch('SELECT id FROM sites WHERE key = :key;', {'key': i_site_key})[0][0]

def add_user(i_site_id: str, i_user_id: str) -> None:
    if not check_valid_site_user(i_user_id, i_site_id):
        db_helper.execute('INSERT INTO sites_users_join (is_manager, user_id, site_id) VALUES (:is_manager, :user_id, :site_id);', 
        {'is_manager': 0, 'user_id': i_user_id, 'site_id': i_site_id})

def remove_user(i_user_to_del_id: str, i_site_id: str, i_user_id: str) -> None:
    if check_valid_site_user(i_user_id, i_site_id):
        db_helper.execute('INSERT INTO sites_users_join_deleted (user_id, site_id, is_manager, deletion_time, deletion_user_id)' +
        f'SELECT :user_id, :site_id, is_manager, :time, :del_uid FROM sites_users_join WHERE user_id = :user_id AND site_id = :site_id;',
        {'time': int(time.time()), 'user_id': i_user_to_del_id, 'del_uid': i_user_id, 'site_id': i_site_id})
        db_helper.execute('DELETE FROM sites_users_join WHERE user_id = :user_id AND site_id = :site_id;',
        {'site_id': i_site_id, 'user_id': i_user_to_del_id,})

def make_manager(i_user_id: str, i_site_id: str) -> None:
    if check_valid_site_user(i_user_id, i_site_id):
        db_helper.execute('UPDATE sites_users_join SET is_manager = :is_manager WHERE user_id = :user_id AND site_id = :site_id;',
        {'user_id': i_user_id, 'site_id': i_site_id, 'is_manager': 1})

def get_sites_from_user(i_user_id: str) -> dict:
    retval = {}
    res = db_helper.fetch('SELECT site_id FROM sites_users_join WHERE user_id = :user_id;', {'user_id': i_user_id})
    for site_id_tup in res:
        retval[site_id_tup[0]] = get_info_from_id(site_id_tup[0])
    return retval

def check_valid_site_user(i_user_id: str, i_site_id: str) -> bool:
    res = db_helper.fetch('SELECT site_id FROM sites_users_join WHERE user_id = :user_id;', {'user_id': i_user_id})
    for site_id_tup in res:
        if i_site_id == site_id_tup[0]:
            return True
    return False

def check_site_manager(i_user_id: str, i_site_id: str) -> bool:
    res = db_helper.fetch('SELECT is_manager FROM sites_users_join WHERE site_id = :site_id AND user_id = :user_id;', 
    {'user_id': i_user_id, 'site_id': i_site_id})
    if len(res) == 1:
        if res[0][0] == 1:
            return True
    return False

