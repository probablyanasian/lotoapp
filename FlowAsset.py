import time
import db_helper
import custom_utils

class FlowAsset:
	def __init__(self, asset_id: str, i_type: str, nom_flow_rate: float, quantity: int, duration: float):
		db_helper.execute("INSERT INTO flow_assets (asset_id, type, nom_flow_rate, quantity, expected_duration) VALUES (:asset_id, :type, :nom_flow_rate, :quantity, :duration);", 
			{'asset_id': asset_id, 'type': i_type, 'nom_flow_rate': nom_flow_rate, 'quantity': quantity, 'duration': duration})
	
def get_info_from_asset(asset_id):
	return db_helper.fetch("SELECT * FROM flow_assets WHERE asset_id = :asset_id;", {'asset_id': asset_id})

def new_flow_asset_record(asset_id: str, flow_rate: float):
	db_helper.execute("INSERT INTO flow_asset_records (asset_id, flow_rate) VALUES (:asset_id, :flow_rate);", 
		{'asset_id': asset_id, "flow_rate": flow_rate})

def delete_flow_asset(asset_id: str, flow_asset_id: int):
	db_helper.execute("DELETE FROM flow_assets WHERE asset_id = :asset_id AND id = :flow_asset_id;", 
		{'asset_id': asset_id, 'flow_asset_id': flow_asset_id})