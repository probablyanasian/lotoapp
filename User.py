import time
import db_helper
import custom_utils
from sqlite3.dbapi2 import Error
from passlib.hash import pbkdf2_sha256

class User:
    def __init__(self, i_fname: str, i_lname: str, i_uname: str, i_pass: str, i_phone: str, i_email: str, i_share_contact: int) -> None:
        self.id = custom_utils.random_id(32)
        self.passwd = pbkdf2_sha256.hash(i_pass)
        try:
            db_helper.execute('INSERT INTO users (id, fname, lname, uname, pass, phone, email, share_contact, archived) VALUES (:id, :fname, :lname, :uname, :pass, :phone, :email, :share_contact, :archived);', 
            {'id': self.id, 'fname': i_fname, 'lname': i_lname, 'uname': i_uname, 'pass': self.passwd, 'phone': i_phone, 'email': i_email, 'share_contact': i_share_contact, 'archived': 0})
        except Error as e:
            print(e)

def update_user(i_user_id: str, i_fname: str, i_lname: str, i_uname: str, i_phone: str, i_email: str, i_share_contact: int) ->  None:
    db_helper.execute('UPDATE users SET fname = :fname, lname = :lname, uname = :uname, phone = :phone, email = :email, share_contact = :share_contact WHERE id = :uid;', 
            {'uid': i_user_id, 'fname': i_fname, 'lname': i_lname, 'uname': i_uname, 'phone': i_phone, 'email': i_email, 'share_contact': i_share_contact, 'archived': 0})
    
def get_info_from_id(i_user_id: str) -> list:
    return db_helper.fetch('SELECT fname, lname, uname, phone, email, share_contact FROM users WHERE id = :id;',
    {'id': i_user_id})

def verify_password(i_uname: str, i_pass: str) -> tuple:
    res = db_helper.fetch('SELECT id, pass FROM users WHERE uname = :i_uname;', {'i_uname': i_uname})
    if len(res) == 1:
        if pbkdf2_sha256.verify(i_pass, res[0][1]):
            return (True, res[0][0])
    return (False,)

def verify_password_by_id(i_user_id: str, i_pass: str) -> bool:
    res = db_helper.fetch('SELECT pass FROM users WHERE id = :user_id;', {'user_id': i_user_id})
    if len(res) == 1:
        if pbkdf2_sha256.verify(i_pass, res[0][0]):
            return True
    return False

def check_exists(i_uname: str) -> bool:
    res = db_helper.fetch('SELECT * FROM users WHERE uname = :i_uname;', {'i_uname': i_uname})
    if len(res) != 0:
        return True
    return False

def change_password(i_id: str, i_pass: str) -> None:
    passwd = pbkdf2_sha256.hash(i_pass)
    db_helper.execute('UPDATE users SET pass = :passwd WHERE id = :id;', {'passwd': passwd, 'id': i_id})

def generate_token(i_id: str) -> str:
    token = custom_utils.random_id(48)

    db_helper.execute('INSERT INTO tokens (token, creation_time, user_id) VALUES (:token, :creation_time, :user_id);', 
    {'token': token, 'creation_time': int(time.time()), 'user_id': i_id})
    
    return token

def validate_token(i_tok: str) -> tuple:
    res = db_helper.fetch('SELECT creation_time, user_id FROM tokens WHERE token = :tok;', {'tok': i_tok})
    if len(res) == 0:
        return (False,)
    if (res[0][0] + 12*60*60) > time.time():
        return (True, res[0][1])
    return (False,)

def get_users_from_incident(i_incident_id: str) -> list:
    return db_helper.fetch('SELECT user_id FROM users_incidents_join WHERE incident_id = :incident_id;', {'incident_id': i_incident_id})

def get_users_names_from_incident(i_incident_id: str) -> list:
    res = db_helper.fetch('SELECT user_id FROM users_incidents_join WHERE incident_id = :incident_id;', {'incident_id': i_incident_id})
    names = []
    for user_id_tup in res:
        names_tup = db_helper.fetch('SELECT fname, lname FROM users WHERE id = :user_id;', {'user_id': user_id_tup[0]})
        for name in names_tup:
            names.append(name[0]+' '+name[1])
    return names

def fake_del_user(i_user_id: str) -> None:
    db_helper.execute('UPDATE users SET uname = :uname, pass = :pass, archived = :arc WHERE id = :user_id;',
    {'uname': custom_utils.random_id(32), 'pass': pbkdf2_sha256.hash(custom_utils.random_id(32)), 'arc': 1})