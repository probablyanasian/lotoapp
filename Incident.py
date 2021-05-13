from Asset import get_assets_from_incident
import time
import Source
import db_helper
import custom_utils

class Incident:
    #l_date is actually created date, locked will be part of source.
    def __init__(self, i_site: str, i_user_id: str, i_reason: str) -> None:
        self.id = custom_utils.random_id(32)
        self.key = custom_utils.random_id(32)
        db_helper.execute('INSERT INTO incidents (id, key, site_id, creator_id, reason, l_date, resolved) VALUES (:id, :key, :site_id, :creator_id, :reason, :l_date, :resolved);', 
        {'id': self.id, 'key': self.key, 'site_id': i_site, 'creator_id': i_user_id, 'reason': i_reason, 'l_date': int(time.time()), 'resolved': 0})
        db_helper.execute('INSERT INTO users_incidents_join (user_id, incident_id, leader) VALUES (:user_id, :incident_id, :leader);', 
        {'user_id': i_user_id, 'incident_id': self.id, 'leader': 1})

def regenKey(i_id: str) -> None:
    key = custom_utils.random_id(32)
    db_helper.execute("UPDATE incidents SET key = :key WHERE id = :id;", {'id': i_id})

def get_info_from_id(i_incident_id: str) -> list: 
    return db_helper.fetch('SELECT reason, l_date, resolved, creator_id FROM incidents WHERE id = :incident_id;',
    {'incident_id': i_incident_id})

def get_incidents_from_site(i_site_id: str) -> list:
    res = db_helper.fetch('SELECT id, l_date, reason FROM incidents WHERE site_id = :site_id;', {'site_id': i_site_id})
    retval = sorted(res, key=lambda x: x[1], reverse=True)
    return retval

def check_is_leader(i_user_id: str, i_incident_id: str) -> bool:
    res = db_helper.fetch('SELECT leader FROM users_incidents_join WHERE user_id = :user_id AND incident_id = :incident_id;',
    {'user_id': i_user_id, 'incident_id': i_incident_id})
    if len(res) > 0:
        if res[0][0]:
            return True
    return False

def resolve(i_incident_id: str) -> None:
    db_helper.execute('UPDATE incidents SET resolved = :resolved WHERE id = :incident_id;',
    {'incident_id': i_incident_id, 'resolved': 1})
    db_helper.execute('UPDATE users_incidents_sources_join SET locked = :locked, final_unlock_time = :cur_time WHERE incident_id = :incident_id',
            {'incident_id': i_incident_id, 'cur_time': int(time.time()), 'locked': 0})
    asset_tup_list = get_assets_from_incident(i_incident_id)
    for asset_tup in asset_tup_list:
        source_tup_list = Source.get_sources_from_asset(asset_tup[0])
        for source_tup in source_tup_list:
            Source.update_locked(source_tup[0])

def is_resolved(i_incident_id: str) -> bool:
    res = db_helper.fetch('SELECT resolved FROM incidents WHERE id = :incident_id;',
    {'incident_id': i_incident_id})
    if len(res) > 0:
        if res[0][0]:
            return True
    return False

def in_incident(i_user_id: str, i_incident_id: str) -> bool:
    res = db_helper.fetch('SELECT * FROM users_incidents_join WHERE user_id = :user_id AND incident_id = :incident_id;',
    {'user_id': i_user_id, 'incident_id': i_incident_id})
    return bool(len(res))

def join_incident(i_user_id: str, i_incident_id: str) -> None:
    if not in_incident(i_user_id, i_incident_id) and not is_resolved(i_incident_id):
        db_helper.execute('INSERT INTO users_incidents_join (user_id, incident_id, leader) VALUES (:user_id, :incident_id, :leader);',
        {'user_id': i_user_id, 'incident_id': i_incident_id, 'leader': 0})
        Source.insert_user_to_incident_source_from_incident(i_user_id, i_incident_id)

def leave_incident(i_user_id: str, i_incident_id: str) -> None:
    if in_incident(i_user_id, i_incident_id) and not is_resolved(i_incident_id):
        db_helper.execute('INSERT INTO users_incidents_join_deleted (user_id, incident_id, leader, deletion_time, deletion_user_id)' +
        f'SELECT user_id, :incident_id, leader, :time, :del_uid FROM users_incidents_join WHERE incident_id = :incident_id AND user_id = :user_id;',
        {'time': int(time.time()), 'del_uid': i_user_id, 'user_id': i_user_id, 'incident_id': i_incident_id})
        db_helper.execute('DELETE FROM users_incidents_join WHERE incident_id = :incident_id AND user_id = :user_id;',
        {'user_id': i_user_id, 'incident_id': i_incident_id})
        Source.remove_user_from_incident_source_from_incident(i_user_id, i_incident_id)

def add_asset_to_incident(i_asset_id: str, i_incident_id: str) -> None:
    if not is_resolved(i_incident_id):
        resOne = db_helper.fetch('SELECT * FROM incidents_assets_join WHERE asset_id = :asset_id AND incident_id = :incident_id;',
        {'asset_id': i_asset_id, 'incident_id': i_incident_id})
        if len(resOne) == 0:
            db_helper.execute('INSERT INTO incidents_assets_join (asset_id, incident_id) VALUES (:asset_id, :incident_id);', 
                {'asset_id': i_asset_id, 'incident_id': i_incident_id})
            
def remove_asset_from_incident(i_asset_id: str, i_incident_id: str, i_user_id: str) -> None:
    if not is_resolved(i_incident_id):
        db_helper.execute('INSERT INTO incidents_assets_join_deleted (incident_id, asset_id, deletion_time, deletion_user_id)' +
        f'SELECT :incident_id, :asset_id, :time, :del_uid FROM incidents_assets_join WHERE incident_id = :incident_id AND asset_id = :asset_id;',
        {'time': int(time.time()), 'del_uid': i_user_id, 'incident_id': i_incident_id, 'asset_id': i_asset_id})
        db_helper.execute('DELETE FROM incidents_assets_join WHERE incident_id = :incident_id AND asset_id = :asset_id;',
        {'incident_id': i_incident_id, 'asset_id': i_asset_id})

def get_incidents_from_asset(i_asset_id: str) -> list:
    incident_id_res = db_helper.fetch('SELECT incident_id FROM incidents_assets_join WHERE asset_id = :asset_id;', {'asset_id': i_asset_id})
    res = []
    for incident_id_tup in incident_id_res:
        res.append(db_helper.fetch('SELECT id, reason, l_date FROM incidents WHERE id = :incident_id;', {'incident_id': incident_id_tup[0]})[0])
    retval = sorted(res, key=lambda x: x[2], reverse=True)
    return retval