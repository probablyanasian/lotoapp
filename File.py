import os
import time
import db_helper
import Incident
import Source
import Asset
import User
import custom_utils
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

class File:
    def __init__(self, i_file: FileStorage, i_root_path: str, i_site_id: str, i_incident_id: str, i_user_id: str, i_source_id: str) -> None:
        self.id = custom_utils.random_id(48)
        self.fpath = os.path.join(i_root_path, i_site_id, i_incident_id, i_user_id, i_source_id, self.id)
        
        #ensure filename is unique
        while os.path.isfile(self.fpath):
            self.id = custom_utils.random_id(48)
            self.fpath = os.path.join(i_root_path, i_site_id, i_incident_id, i_user_id, i_source_id, self.id)

        os.makedirs(os.path.join(i_root_path, i_site_id, i_incident_id, i_user_id, i_source_id), exist_ok=True)
        i_file.save(self.fpath)
        
        db_helper.execute('INSERT INTO files (id, fpath, user_id, site_id, incident_id, source_id, time) VALUES (:id, :fpath, :user_id, :site_id, :incident_id, :source_id, :time);', 
        {'id': self.id, 'fpath': self.fpath, 'user_id': i_user_id, 'site_id': i_site_id, 'incident_id': i_incident_id, 'source_id': i_source_id, 'time': int(time.time())})
        
def get_info_by_id(i_file_id: str) -> list:
    return db_helper.fetch('SELECT fpath, user_id, site_id, incident_id, source_id, time FROM files WHERE id = :file_id;',
    {'file_id': i_file_id})

def get_files_by_ids(i_site_id: str, i_incident_id: str, i_user_id: str, i_source_id: str) -> list:
    return db_helper.fetch('SELECT id, fpath, time FROM files WHERE site_id = :site_id AND user_id = :user_id AND incident_id = :incident_id AND source_id = :source_id;',
    {'site_id': i_site_id, 'user_id': i_user_id, 'incident_id': i_incident_id, 'source_id': i_source_id})

def get_exists(i_site_id: str, i_incident_id: str, i_user_id, i_source_id: str) -> bool:
    res = db_helper.fetch('SELECT id, fpath, time FROM files WHERE site_id = :site_id AND user_id = :user_id AND incident_id = :incident_id AND source_id = :source_id;',
    {'site_id': i_site_id, 'user_id': i_user_id, 'incident_id': i_incident_id, 'source_id': i_source_id})
    if len(res) != 0:
        return True
    return False

def incident_source_with_no_file(i_site_id: str) -> list:
    #TODO: do this.
    retval = []
    incident_info_tup_list = Incident.get_incidents_from_site(i_site_id)
    for incident_info_tup in incident_info_tup_list:
        user_info_tup_list = User.get_users_from_incident(incident_info_tup[0])
        for user_info_tup in user_info_tup_list:
            asset_info_tup_list = Asset.get_assets_id_from_incident(incident_info_tup[0])
            print('asset_tup')
            print(asset_info_tup_list)
            for asset_info_tup in asset_info_tup_list:
                source_info_tup_list = Source.get_info_from_asset(asset_info_tup[0])
                print('source_tup')
                print(source_info_tup_list)
                for source_info_tup in source_info_tup_list:
                    print(user_info_tup[0], incident_info_tup[0], asset_info_tup[0], source_info_tup[0])
                    if not get_exists(i_site_id, incident_info_tup[0], user_info_tup[0], source_info_tup[0]):
                        retval.append((user_info_tup[0], incident_info_tup[0], asset_info_tup[0], source_info_tup[0]))
    print(retval)
    return retval