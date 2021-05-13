import time
import db_helper
import custom_utils

class Asset:
    def __init__(self, i_creator: str, i_site: str, i_name: str, i_location: str, i_manu: str, i_model: str, i_serial_num: str, i_shutoff_ins: str, i_startup_ins: str) -> None:
        self.id = custom_utils.random_id(32)
        self.key = custom_utils.random_id(32)

        db_helper.execute('INSERT INTO assets (id, key, creator_id, site_id, name, location, archived, ' + 
        'manufacturer, model_number, serial_number, shutoff_instructions, startup_instructions, creation_time, last_updated_time, ' +
        ') VALUES (:id, :key, :creator_id, :site_id, :name, :location, :archived, ' +
        ':manufacturer, :model_number, :serial_number, :shutoff_instructions, :startup_instructions, :creation_time, :last_updated_time);', 
        {'id': self.id, 'key': self.key, 'creator_id': i_creator, 'site_id': i_site, 'name': i_name, 'location': i_location, 'archived': 0,
        'manufacturer': i_manu, 'model_number': i_model, 'serial_number': i_serial_num, 'shutoff_instructions': i_shutoff_ins,
        'startup_instructions': i_startup_ins, 'creation_time': int(time.time()), 'last_updated_time': int(time.time())})

def regenKey(i_id: str) -> None:
    key = custom_utils.random_id(32)
    db_helper.execute("UPDATE assets SET key = :key WHERE id = :id;", {'id': i_id, 'key': key})

def get_info_from_asset(i_asset_id: str) -> tuple:
    return db_helper.fetch('SELECT name, location FROM assets WHERE id = :asset_id;', {'asset_id': i_asset_id})[0]

# def insert_asset_to_incident(i_asset_id: str, i_incident_id: str, i_name: str) -> None:
#     db_helper.execute('INSERT INTO incidents_assets_join (incident_id, asset_id, name) VALUES (:incident_id, :asset_id, :name);', 
#     {'incident_id': i_incident_id, 'asset_id': i_asset_id, 'name': i_name})

def get_assets_from_incident(i_incident_id: str) -> list:
    res = db_helper.fetch('SELECT asset_id FROM incidents_assets_join WHERE incident_id = :incident_id;', {'incident_id': i_incident_id})
    ret = [(get_info_from_asset(tup[0])[0], tup[0]) for tup in res]
    retval = sorted(ret, key=lambda x: x[0])
    return retval

def get_assets_from_site(i_site_id: str) -> list:
    res = db_helper.fetch('SELECT id, name, location FROM assets WHERE site_id = :site_id;', {'site_id': i_site_id})
    return res

def get_assets_from_site_not_match_incident(i_site_id: str, i_incident_id: str) -> list:
    resOne = get_assets_from_site(i_site_id)
    resTwo = db_helper.fetch('SELECT asset_id FROM incidents_assets_join WHERE incident_id = :incident_id;', {'incident_id': i_incident_id})
    resTwoFilt = [filt[0] for filt in resTwo]
    return [filt for filt in resOne if filt[0] not in resTwoFilt]

def delete_asset(i_user_id: str, i_asset_id: str) -> None:
    db_helper.execute('INSERT INTO assets_deleted (id, key, creator_id, site_id, name, location, archived, '
        + 'manufacturer, model_number, serial_number, shutoff_instructions, startup_instructions, creation_time, last_updated_time, '
        + 'deletion_time, deletion_user_id)' +
        f'SELECT id, key, creator_id, site_id, name, location, archived, ' + 
        'manufacturer, model_number, serial_number, shutoff_instructions, startup_instructions, creation_time, last_updated_time, ' + 
        ':time, :del_uid FROM assets WHERE id = :asset_id;',
        {'time': int(time.time()), 'del_uid': i_user_id, 'asset_id': i_asset_id})
    db_helper.execute('DELETE FROM assets WHERE id = :asset_id;', {'asset_id': i_asset_id})
    db_helper.execute('INSERT INTO sources_assets_join_deleted (asset_id, source_id, deletion_time, deletion_user_id)' +
            f'SELECT asset_id, source_id, :time, :del_uid FROM sources_assets_join WHERE asset_id = :asset_id;',
            {'time': int(time.time()), 'del_uid': i_user_id, 'asset_id': i_asset_id})
    db_helper.execute('DELETE FROM sources_assets_join WHERE asset_id = :asset_id;', {'asset_id': i_asset_id})
    db_helper.execute('INSERT INTO incidents_assets_join_deleted (incident_id, asset_id, deletion_time, deletion_user_id)' +
            f'SELECT incident_id, asset_id, :time, :del_uid FROM incidents_assets_join WHERE asset_id = :asset_id;',
            {'time': int(time.time()), 'del_uid': i_user_id, 'asset_id': i_asset_id})
    db_helper.execute('DELETE FROM incidents_assets_join WHERE asset_id = :asset_id;', {'asset_id': i_asset_id})

    
def add_source_to_asset(i_asset_id: str, i_source_id: str) -> None:
    resOne = db_helper.fetch('SELECT * FROM sources_assets_join WHERE asset_id = :asset_id AND source_id = :source_id;',
    {'asset_id': i_asset_id, 'source_id': i_source_id})
    if len(resOne) == 0:
        db_helper.execute('INSERT INTO sources_assets_join (asset_id, source_id) VALUES (:asset_id, :source_id);',
        {'asset_id': i_asset_id, 'source_id': i_source_id})

def get_assets_from_source(i_source_id: str) -> list:
    return db_helper.fetch('SELECT asset_id FROM sources_assets_join WHERE source_id = :source_id;', {'source_id': i_source_id})