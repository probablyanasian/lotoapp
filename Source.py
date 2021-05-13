import time
import Site
import User
import Asset
import Incident
import db_helper
import custom_utils

class Source:
    def __init__(self, i_site: str, i_user_id: str, i_name: str, i_location: str, i_type: str, i_magnitude: str, i_private: int, i_shutoff_ins: str, i_startup_ins: str, i_verif_ins: str) -> None:
        self.id = custom_utils.random_id(32)

        db_helper.execute('INSERT INTO sources (id, site_id, creator_id, name, location, type, magnitude, locked, private, archived, shutoff_instructions, startup_instructions, verification_instructions, creation_time, last_updated_time)' +
        'VALUES (:id, :site_id, :creator_id, :name, :location, :type, :magnitude, :locked, :private, :archived, :shutoff_instructions, :startup_instructions, :verification_instructions, :creation_time, :last_updated_time);', 
        {'id': self.id, 'site_id': i_site, 'creator_id': i_user_id, 'name': i_name, 'location': i_location, 'type': i_type, 'magnitude': i_magnitude, 'locked': 0, 'archived': 0, 'private': i_private,
        'shutoff_instructions': i_shutoff_ins, 'startup_instructions': i_startup_ins, 'verification_instructions': i_verif_ins, 'creation_time': int(time.time()), 'last_updated_time': int(time.time())})

def update_by_id(i_source_id: str, i_name: str, i_location: str, i_type: str, i_magnitude: str, i_shutoff_ins: str, i_startup_ins: str, i_verif_ins: str, i_private: str) -> None:
    db_helper.execute('UPDATE sources SET name = :name, location = :location, type = :type, magnitude = :magnitude, private = :private, shutoff_instructions = :shutoff_instructions, ' + 
    'startup_instructions = :startup_instructions, verification_instructions = :verification_instructions, last_updated_time = :last_updated_time WHERE id = :source_id',
    {'source_id': i_source_id, 'name': i_name, 'location': i_location, 'type': i_type, 'magnitude': i_magnitude, 'private': i_private, 'shutoff_instructions': i_shutoff_ins,
    'startup_instructions': i_startup_ins, 'verification_instructions': i_verif_ins, 'last_updated_time': int(time.time())})

def get_locked_sources_from_site(i_site_id: str):
    return db_helper.fetch('SELECT id, name, location FROM sources WHERE site_id = :site_id AND locked = 1;',
    {'site_id': i_site_id})

def get_info_from_id(i_source_id: str) -> list:
    return db_helper.fetch('SELECT name, location, type, magnitude, locked, site_id, shutoff_instructions, startup_instructions, verification_instructions, creation_time, last_updated_time, private FROM sources WHERE id = :source_id;',
    {'source_id': i_source_id})

def get_sources_from_asset(i_asset_id: str) -> list:
    return db_helper.fetch('SELECT source_id FROM sources_assets_join WHERE asset_id = :asset_id;',
    {'asset_id': i_asset_id})

def insert_user_to_incident_source(i_user_id: str, i_incident_id: str, i_source_id: str, i_locked: int) -> None:
    db_helper.execute('INSERT INTO users_incidents_sources_join (user_id, incident_id, source_id, locked, was_locked) VALUES (:user_id, :incdent_id, :source_id, :locked, :was_locked);',
    {'user_id': i_user_id, 'incdent_id': i_incident_id, 'source_id': i_source_id, 'locked': i_locked, 'was_locked': i_locked})
    update_locked(i_source_id)

def insert_user_to_incident_source_from_incident(i_user_id: str, i_incident_id: str) -> None:
    asset_tup_list = Asset.get_assets_from_incident(i_incident_id)
    for asset_tup in asset_tup_list:
        source_tup_list = get_sources_from_asset(asset_tup[1])
        for source_tup in source_tup_list:
            insert_user_to_incident_source(i_user_id, i_incident_id, source_tup[0], 0)

def remove_user_from_incident_source_from_incident(i_user_id: str, i_incident_id: str) -> None:
    db_helper.execute('INSERT INTO users_incidents_sources_join_deleted (user_id, incident_id, source_id, locked, was_locked, deletion_time, deletion_user_id)' +
    f'SELECT :user_id, :incident_id, source_id, locked, was_locked, :time, :del_uid FROM users_incidents_sources_join WHERE incident_id = :incident_id AND user_id = :user_id;',
    {'time': int(time.time()), 'del_uid': i_user_id, 'user_id': i_user_id, 'incident_id': i_incident_id})
    db_helper.execute('DELETE FROM users_incidents_sources_join WHERE incident_id = :incident_id AND user_id = :user_id;',
    {'user_id': i_user_id, 'incident_id': i_incident_id})
    asset_tup_list = Asset.get_assets_from_incident(i_incident_id)
    for asset_tup in asset_tup_list:
        source_tup_list = get_sources_from_asset(asset_tup[1])
        for source_tup in source_tup_list:
            update_locked(source_tup[0])

def get_users_status_from_source(i_source_id: str) -> list:
    return db_helper.fetch('SELECT user_id, locked, incident_id FROM users_incidents_sources_join WHERE source_id = :source_id;', {'source_id': i_source_id})

def get_users_status_from_source_ignore_resolved(i_source_id: str) -> list:
    info_tup_list = get_users_status_from_source(i_source_id)
    temp_pack = []
    for user_tup in info_tup_list:
        if not Incident.is_resolved(user_tup[2]):
            user_info = User.get_info_from_id(user_tup[0]) 
            temp_pack.append([*user_tup, *user_info[0]])
    return temp_pack

def get_users_info_from_source(i_source_id: str) -> list:
    user_tup_list = get_users_status_from_source(i_source_id)
    retval = []
    for user_tup in user_tup_list:
        user_info = User.get_info_from_id(user_tup[0]) 
        retval.append([*user_tup, *user_info[0]])
    return list(set(retval)) # cheap tactic out

def get_users_status_from_incident_source(i_incident_id: str, i_source_id: str) -> list:
    return db_helper.fetch('SELECT user_id, locked FROM users_incidents_sources_join WHERE source_id = :source_id AND incident_id = :incident_id',
    {'source_id': i_source_id, 'incident_id': i_incident_id})

def all_users_incident_source_locked(i_incident_id: str, i_source_id: str) -> bool:
    res = get_users_status_from_incident_source(i_incident_id, i_source_id)
    if len(res) == 0:
        return False
    for res_tup in res:
        if not res_tup[1]:
            return False
    return True

def get_user_was_locked(i_user_id: str, i_incident_id: str, i_source_id: str) -> bool:
    res = db_helper.fetch('SELECT was_locked FROM users_incidents_sources_join WHERE user_id = :user_id AND incident_id = :incident_id AND source_id = :source_id;',
          {'user_id': i_user_id, 'incident_id': i_incident_id, 'source_id': i_source_id})
    if len(res) > 0:
        return bool(res[0][0])
    return False 

def update_user_locked(i_user_id: str, i_incident_id: str, i_source_id: str, i_locked: int) -> None:
    if not Incident.is_resolved(i_incident_id) or get_user_locked_incident_source(i_user_id, i_incident_id, i_source_id):
        if i_locked and not get_user_was_locked(i_user_id, i_incident_id, i_source_id):
            db_helper.execute('UPDATE users_incidents_sources_join SET locked = :locked, was_locked = :locked, initial_lock_time = :cur_time WHERE user_id = :user_id AND incident_id = :incident_id AND source_id = :source_id;',
            {'user_id': i_user_id, 'incident_id': i_incident_id, 'source_id': i_source_id, 'locked': i_locked, 'cur_time': int(time.time())})
        elif i_locked:
            db_helper.execute('UPDATE users_incidents_sources_join SET locked = :locked, was_locked = :locked WHERE user_id = :user_id AND incident_id = :incident_id AND source_id = :source_id;',
            {'user_id': i_user_id, 'incident_id': i_incident_id, 'source_id': i_source_id, 'locked': i_locked})
        else:
            db_helper.execute('UPDATE users_incidents_sources_join SET locked = :locked, final_unlock_time = :cur_time WHERE user_id = :user_id AND incident_id = :incident_id AND source_id = :source_id;',
            {'user_id': i_user_id, 'incident_id': i_incident_id, 'source_id': i_source_id, 'locked': i_locked, 'cur_time': int(time.time())})
    update_locked(i_source_id)

def update_locked(i_source_id: str):
    res = db_helper.fetch('SELECT locked FROM users_incidents_sources_join WHERE source_id = :source_id;', {'source_id': i_source_id})
    locked = False
    for locked_tup in res:
        if locked_tup[0]:
            locked = True
            break
    db_helper.execute('UPDATE sources SET locked = :locked WHERE id = :source_id;', 
    {'locked': locked, 'source_id': i_source_id})

def connect_source_to_asset(i_source_id: str, i_asset_id: str, i_name: str) -> None:
    db_helper.execute('INSERT INTO sources_assets_join (source_id, asset_id, name) VALUES (:source_id, :asset_id, :name);',
    {'source_id': i_source_id, 'asset_id': i_asset_id, 'name': i_name})

def remove_source_from_asset(i_source_id: str, i_asset_id: str, i_user_id: str) -> None:
    db_helper.execute('INSERT INTO sources_assets_join_deleted (asset_id, source_id, deletion_time, deletion_user_id)' +
    f'SELECT :asset_id, :source_id, :time, :del_uid FROM sources_assets_join WHERE source_id = :source_id AND asset_id = :asset_id;',
    {'time': int(time.time()), 'del_uid': i_user_id, 'source_id': i_source_id, 'asset_id': i_asset_id})
    db_helper.execute('DELETE FROM sources_assets_join WHERE source_id = :source_id AND asset_id = :asset_id;',
    {'source_id': i_source_id, 'asset_id': i_asset_id})

def delete_source(i_source_id: str, i_user_id: str) -> None:
    asset_tup_list = Asset.get_assets_from_source(i_source_id)
    for asset_tup in asset_tup_list:
        remove_source_from_asset(i_source_id, asset_tup[0], i_user_id)
    db_helper.execute('INSERT INTO sources_deleted (id, site_id, creator_id, name, location, type, magnitude, locked, archived, ' +
        'shutoff_instructions, startup_instructions, verification_instructions, creation_time, last_updated_time, deletion_time, deletion_user_id)' +
        f'SELECT id, site_id, creator_id, name, location, type, magnitude, locked, archived, ' + 
        'shutoff_instructions, startup_instructions, verification_instructions, creation_time, last_updated_time, :time, :del_uid FROM sources WHERE id = :source_id;',
    {'time': int(time.time()), 'del_uid': i_user_id, 'source_id': i_source_id})
    db_helper.execute('DELETE FROM sources WHERE id = :source_id;', {'source_id': i_source_id})

def get_info_from_asset(i_asset_id: str) -> list:
    source_list = get_sources_from_asset(i_asset_id)
    retval = []
    for source_tup in source_list:
        res = db_helper.fetch('SELECT id, name, locked, location, type, magnitude FROM sources WHERE id = :source_id;', {'source_id': source_tup[0]})[0]
        retval.append(res)
    return retval

def get_user_locked_incident_source(i_user_id: str, i_incident_id: str, i_source_id: str) -> bool:
    res = db_helper.fetch('SELECT locked FROM users_incidents_sources_join WHERE user_id = :user_id AND incident_id = :incident_id AND source_id = :source_id;',
    {'user_id': i_user_id, 'incident_id': i_incident_id, 'source_id': i_source_id})
    if len(res) > 0:
        return res[0][0]
    return 0

def get_info_from_asset_incident(i_user_id: str, i_incident_id: str, i_asset_id: str) -> list:
    source_list = get_sources_from_asset(i_asset_id)
    retval = []
    for source_tup in source_list:
        res = list(db_helper.fetch('SELECT id, name, locked, location, type, magnitude FROM sources WHERE id = :source_id;', {'source_id': source_tup[0]})[0])
        res.append(all_users_incident_source_locked(i_incident_id, source_tup[0]))
        res.append(get_user_locked_incident_source(i_user_id, i_incident_id, source_tup[0]))
        retval.append(res)
    return retval

def get_info_from_site(i_site_id: str) -> list:
    return db_helper.fetch('SELECT id, name, locked, location, type, magnitude FROM sources WHERE site_id = :site_id;', {'site_id': i_site_id})

def get_num_joins(i_source_id: str) -> list:
    res = db_helper.fetch('SELECT asset_id FROM sources_assets_join WHERE source_id = :source_id;', 
    {'source_id': i_source_id})
    return len(res)

def get_info_from_site_restrict_private(i_site_id: str) -> list:
    res = db_helper.fetch('SELECT id, name, locked, location, type, magnitude, private FROM sources WHERE site_id = :site_id;',
    {'site_id': i_site_id})
    return [filt for filt in res if filt[6] == 0 or get_num_joins(filt[0]) == 0]

def get_source_from_site_not_match_asset(i_site_id: str, i_asset_id: str) -> list:
    resOne = get_info_from_site_restrict_private(i_site_id)
    resTwo = db_helper.fetch('SELECT source_id FROM sources_assets_join WHERE asset_id = :asset_id;', {'asset_id': i_asset_id})
    resTwoFilt = [filt[0] for filt in resTwo]
    return [filt for filt in resOne if filt[0] not in resTwoFilt]