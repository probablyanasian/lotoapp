import os
import time
import datetime
import itertools
import Site
import User
import Incident
import Asset
import Source
import File
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, make_response
from werkzeug.utils import secure_filename

DEBUG = True
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'dict'}
def verify_exists(i_to_verif: dict, keys: list) -> bool:
    for key in keys:
        if key not in i_to_verif:
            return False
        else:
            if not i_to_verif[key].strip():
                return False
            if key not in ['verif_ins', 'startup_ins', 'shutoff_ins']:
                if len(i_to_verif[key]) > 350:
                    return False
    return True

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        vals = request.form.to_dict()
        if verify_exists(vals, ['uname', 'pass']):
            if User.verify_password(vals['uname'], vals['pass'])[0]:
                user_id = User.verify_password(vals['uname'], vals['pass'])[1]
                resp = make_response(redirect(url_for('view_sites')))
                tok = User.generate_token(user_id)
                resp.set_cookie('token', tok, expires=int(time.time()+12*60*60))
                return resp
        return render_template('login.html', message='Invalid user or password')
    else:
        resp = make_response(render_template('login.html'))
        resp.set_cookie('token', '', expires=0)
        return resp

@app.route('/logout', methods=['GET'])
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('token', '', expires=0)
    return resp

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        vals = request.form.to_dict()
        if not verify_exists(vals, ['fname', 'lname', 'uname', 'pass', 'verify_pass', 'phone']):
            return render_template('signup.html', message='Missing Parameter')

        if User.check_exists(vals['uname']):
            return render_template('signup.html', message='Username Taken')

        if 'email' not in vals:
            vals['email'] = ''
        
        if vals['pass'] != vals['verify_pass']:
            return render_template('signup.html', message='Passwords do not match')

        share_contact = 1 if 'share_contact' in vals else 0
        User.User(vals['fname'], vals['lname'], vals['uname'], vals['pass'], vals['phone'], vals['email'], share_contact)
        return redirect(url_for('login'))
    else:
        return render_template('signup.html')

@app.route('/new_site', methods=['GET', 'POST'], strict_slashes=False)
def new_site():
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    if request.method == 'POST':
        vals = request.form.to_dict()
        if verify_exists(vals, ['name', 'location']):
            Site.Site(vals['name'], verify[1], vals['location'])
            return redirect(url_for('view_sites'))
        else:
            return render_template('new_site.html', message='Missing Parameter')
    else:
        return render_template('new_site.html')

@app.route('/view_sites', methods=['GET'], strict_slashes=False)
def view_sites():
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    site_dict = Site.get_sites_from_user(verify[1])
    return render_template('view_sites.html', data=site_dict)

@app.route('/join_site', methods=['GET', 'POST'])
def join_site():
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp

    if request.method == 'POST':
        vals = request.form.to_dict()
        if verify_exists(vals, ['key']):
            if Site.check_key(vals['key']):
                site_id = Site.get_id_from_key(vals['key'])
                Site.add_user(site_id, verify[1])
                return redirect(url_for('view_sites'))
            else:
                return render_template('join_site.html', message='Invalid Key')
        else:
            return render_template('join_site.html', message='Missing Parameter')
    else:
        return render_template('join_site.html')

@app.route('/edit_user', methods=['GET', 'POST'])
def edit_user():
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp

    if request.method == 'POST':
        vals = request.form.to_dict()
        if verify_exists(vals, ['action']):
            if vals['action'] == "Delete User":
                User.fake_del_user(verify[1])
        
        user_info = User.get_info_from_id(verify[1])[0]
        if not verify_exists(vals, ['fname', 'lname', 'uname', 'pass', 'phone']):
            return render_template('edit_user.html', user_info=user_info, message='Missing Parameter')

        if vals['uname'] != user_info[2] and User.check_exists(vals['uname']):
            return render_template('edit_user.html', user_info=user_info, message='Username Taken')

        if 'email' not in vals:
            vals['email'] = ''

        share_contact = 1 if 'share_contact' in vals else 0
        if not User.verify_password_by_id(verify[1], vals['pass']):
            return render_template('edit_user.html', user_info=user_info, message='Invalid Password')
        User.update_user(verify[1], vals['fname'], vals['lname'], vals['uname'], vals['phone'], vals['email'], share_contact)
        return redirect(request.url)
    else:
        user_info = User.get_info_from_id(verify[1])[0]
        return render_template('edit_user.html', user_info=user_info)

@app.route('/site/<site_id>/', methods=['GET', 'POST'])
def view_site(site_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return make_response(redirect(url_for('view_sites')))

    if request.method == 'POST':
        if Site.check_site_manager(verify[1], site_id):
            vals = request.form.to_dict()
            if verify_exists(vals, ['action']):
                if vals['action'] == 'Delete Site':
                    Site.delete_site(site_id, verify[1])
                    return redirect(url_for('view_sites'))
                elif vals['action'] == 'Regen Key':
                    Site.regenKey(site_id)
                    return redirect(url_for('view_site', site_id=site_id))
    else:
        if Site.check_site_manager(verify[1], site_id):
            return render_template('site.html', key=Site.get_key_from_id(site_id), is_manager=True)
        return render_template('site.html', is_manager=False)

@app.route('/site/<site_id>/view_locked_sources/')
def view_locked_sources(site_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return make_response(redirect(url_for('view_sites')))

    sources_list = Source.get_locked_sources_from_site(site_id)
    site_name, site_location = Site.get_info_from_id(site_id)
    return render_template('locked_sources.html', sources_list=sources_list, site_name=site_name, site_location=site_location)

@app.route('/site/<site_id>/view_assets/')
def view_assets(site_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return make_response(redirect(url_for('view_sites')))

    asset_list = Asset.get_assets_from_site(site_id)
    return render_template('view_assets.html', data=asset_list)

@app.route('/site/<site_id>/asset/<asset_id>/', methods=['GET', 'POST'], strict_slashes=False)
def base_view_asset(site_id, asset_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))

    if request.method == 'POST':
        if Site.check_site_manager(verify[1], site_id):
            vals = request.form.to_dict()
            if verify_exists(vals, ['action']):
                if vals['action'] == 'Delete Asset':
                    Asset.delete_asset(verify[1], asset_id)
                    return redirect(url_for('view_assets', site_id=site_id))
    else:
        incident_list = Incident.get_incidents_from_asset(asset_id)
        asset_info = Asset.get_info_from_id(asset_id)
        creation_time = time.ctime(asset_info[8])
        last_updated = time.ctime(asset_info[9])
        is_manager = Site.check_site_manager(verify[1], site_id)
        source_list = Source.get_info_from_asset(asset_id)
        return render_template('asset.html', list_incidents=True, incident_list=incident_list, source_list=source_list, asset_info=asset_info, is_manager=is_manager, creation_time=creation_time, last_updated=last_updated)

@app.route('/site/<site_id>/new_asset/', methods=['GET', 'POST'], strict_slashes=False)
def base_new_asset(site_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp

    if not Site.check_valid_site_user(verify[1], site_id):
        return make_response(redirect(url_for('view_sites')))

    if request.method == 'POST':
        vals = request.form.to_dict()
        if verify_exists(vals, ['name', 'location', 'manu', 'model_num', 'serial_num', 'shutoff_ins', 'startup_ins', 'verif_ins']):
            Asset.Asset(verify[1], site_id, vals['name'], vals['location'], vals['manu'], vals['model_num'], vals['serial_num'],
            vals['shutoff_ins'], vals['startup_ins'], vals['verif_ins'])
            return redirect(url_for('view_assets', site_id=site_id))
        else:
            return render_template('new_asset.html', message='Missing Parameter')
    else:
        return render_template('new_asset.html')

@app.route('/site/<site_id>/asset/<asset_id>/add_source', methods=['GET', 'POST'], strict_slashes=False)
def base_add_source(site_id, asset_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return make_response(redirect(url_for('view_sites')))

    if request.method == 'POST':
        vals = request.form.to_dict()
        if verify_exists(vals, ['id']):
            Asset.add_source_to_asset(asset_id, vals['id'])
            return redirect(url_for('base_view_asset', site_id=site_id, asset_id=asset_id))
        else:
            return render_template('add_source.html', message='Missing Parameter')
    else:
        source_list = Source.get_source_from_site_not_match_asset(site_id, asset_id)
        return render_template('add_source.html', source_list=source_list)

def handle_new_source(i_site_id: str, i_user_id: str, i_asset_id: str, i_vals: dict) -> tuple:
    if not verify_exists(i_vals, ['name', 'location', 'type', 'shutoff_ins', 'startup_ins', 'verif_ins']):
            return (False, render_template('new_source.html', message='Missing Parameter'))
    i_vals['private'] = 0 if 'private' not in i_vals else 1
    if 'magnitude' not in i_vals:
        i_vals['magnitude'] = ''
    source_instance = Source.Source(i_site_id, i_user_id, i_vals['name'], i_vals['location'], i_vals['type'], i_vals['magnitude'], i_vals['private'], i_vals['shutoff_ins'], i_vals['startup_ins'], i_vals['verif_ins'])
    Asset.add_source_to_asset(i_asset_id, source_instance.id)
    return (True, source_instance.id, i_vals['private'])

@app.route('/site/<site_id>/asset/<asset_id>/new_source/', methods=['GET', 'POST'], strict_slashes=False)
def base_new_source(site_id, asset_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp

    if not Site.check_valid_site_user(verify[1], site_id):
        return make_response(redirect(url_for('view_sites')))

    if request.method == 'POST':
        vals = request.form.to_dict()
        new_source_resp = handle_new_source(site_id, verify[1], asset_id, vals)
        if not new_source_resp[0]:
            return new_source_resp[1]
        return redirect(url_for('base_view_asset', site_id=site_id, asset_id=asset_id))
    else:
        return render_template('new_source.html')

@app.route('/site/<site_id>/view_incidents/', methods=['GET'])
def view_incidents(site_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return make_response(redirect(url_for('view_sites')))

    incident_dict = Incident.get_incidents_from_site(site_id)
    return render_template('view_incidents.html', data=incident_dict)

@app.route('/site/<site_id>/new_incident/', methods=['GET', 'POST'])
def new_incident(site_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return make_response(redirect(url_for('view_sites')))

    if request.method == 'POST':
        vals = request.form.to_dict()
        if verify_exists(vals, ['reason']):
            Incident.Incident(site_id, verify[1], vals['reason'])
            return redirect(url_for('view_incidents', site_id=site_id))
        else:
            return render_template('new_incident.html', message='Missing Parameter', time=datetime.datetime.now().isoformat())
    else:
        return render_template('new_incident.html', time=datetime.datetime.now().isoformat())

@app.route('/site/<site_id>/incident/<incident_id>/', methods=['GET', 'POST'])
def view_incident(site_id, incident_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return make_response(redirect(url_for('view_sites')))

    if request.method == 'POST':
        vals = request.form.to_dict()
        if verify_exists(vals, ['action']):
            if vals['action'] == 'Join Incident':
                Incident.join_incident(verify[1], incident_id)
                return redirect(url_for('view_incident', site_id=site_id, incident_id=incident_id))
            elif vals['action'] == 'Leave Incident':
                Incident.leave_incident(verify[1], incident_id)
                return redirect(url_for('view_incident', site_id=site_id, incident_id=incident_id))
            elif vals['action'] == 'Resolve Incident':
                if Incident.check_is_leader(verify[1], incident_id):
                    Incident.resolve(incident_id)
                    return redirect(request.url)
    else:
        incident_info = Incident.get_info_from_id(incident_id)[0]
        asset_list = Asset.get_assets_from_incident(incident_id)
        name_list = User.get_users_names_from_incident(incident_id)
        user_in = Incident.in_incident(verify[1], incident_id)
        is_leader = Incident.check_is_leader(verify[1], incident_id)
        is_resolved = Incident.is_resolved(incident_id)
        return render_template('incident.html', name=incident_info[0], asset_list=asset_list, names=name_list, in_incident=user_in, is_leader=is_leader, is_resolved=is_resolved)

@app.route('/site/<site_id>/incident/<incident_id>/add_asset/', methods=['GET', 'POST'])
def add_asset(site_id, incident_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return make_response(redirect(url_for('view_sites')))

    if Incident.is_resolved(incident_id):
        return redirect(url_for('view_incident', site_id=site_id, incident_id=incident_id))

    if request.method == 'POST':
        vals = request.form.to_dict()
        if verify_exists(vals, ['id']):
            Incident.add_asset_to_incident(vals['id'], incident_id)
            user_list = User.get_users_from_incident(incident_id)
            Source.insert_user_to_incident_source_from_incident(verify[1], incident_id)
            return redirect(url_for('view_incident', site_id=site_id, incident_id=incident_id))
        else:
            return render_template('add_asset.html', message='Missing Parameter')
    else:
        asset_list = Asset.get_assets_from_site_not_match_incident(site_id, incident_id)
        return render_template('add_asset.html', asset_list=asset_list)

@app.route('/site/<site_id>/incident/<incident_id>/new_asset/', methods=['GET', 'POST'], strict_slashes=False)
def new_asset(site_id, incident_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp

    if not Site.check_valid_site_user(verify[1], site_id):
        return make_response(redirect(url_for('view_sites')))

    if Incident.is_resolved(incident_id):
        return redirect(url_for('view_incident', site_id=site_id, incident_id=incident_id))

    if request.method == 'POST':
        vals = request.form.to_dict()
        if verify_exists(vals, ['name', 'location', 'manu', 'model_num', 'serial_num', 'shutoff_ins', 'startup_ins', 'verif_ins']):
            asset_instance = Asset.Asset(verify[1], site_id, vals['name'], vals['location'], vals['manu'], vals['model_num'], vals['serial_num'],
            vals['shutoff_ins'], vals['startup_ins'], vals['verif_ins'])
            Incident.add_asset_to_incident(asset_instance.id, incident_id)
            return redirect(url_for('view_incident', site_id=site_id, incident_id=incident_id))
        else:
            return render_template('new_asset.html', message='Missing Parameter')
    else:
        return render_template('new_asset.html')

@app.route('/site/<site_id>/incident/<incident_id>/asset/<asset_id>/', methods=['GET', 'POST'], strict_slashes=False)
def view_asset(site_id, incident_id, asset_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))

    if request.method == 'POST':
        if Site.check_site_manager(verify[1], site_id):
            vals = request.form.to_dict()
            if verify_exists(vals, ['action']):
                if vals['action'] == 'Delete Asset':
                    Asset.delete_asset(verify[1], asset_id)
                    return redirect(url_for('view_incident', site_id=site_id, incident_id=incident_id))
                elif vals['action'] == 'Remove Asset From Incident':
                    Incident.remove_asset_from_incident(asset_id, incident_id, verify[1])
                    return redirect(url_for('view_incident', site_id=site_id, incident_id=incident_id))
                else:
                    asset_info = Asset.get_info_from_id(asset_id)
                    creation_time = time.ctime(asset_info[8])
                    last_updated = time.ctime(asset_info[9])
                    is_manager = Site.check_site_manager(verify[1], site_id)
                    source_list = Source.get_info_from_asset_incident(verify[1], incident_id, asset_id)
                    return render_template('incident_asset.html', asset_info=asset_info, source_list=source_list, is_manager=is_manager, creation_time=creation_time, last_updated=last_updated, message="Invalid Request")
    else:
        asset_info = Asset.get_info_from_id(asset_id)
        creation_time = time.ctime(asset_info[8])
        last_updated = time.ctime(asset_info[9])
        is_manager = Site.check_site_manager(verify[1], site_id)
        source_list = Source.get_info_from_asset_incident(verify[1], incident_id, asset_id)
        return render_template('incident_asset.html', asset_info=asset_info, source_list=source_list, is_manager=is_manager, creation_time=creation_time, last_updated=last_updated)

@app.route('/site/<site_id>/incident/<incident_id>/asset/<asset_id>/add_source/', methods=['GET', 'POST'])
def add_source(site_id, incident_id, asset_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return make_response(redirect(url_for('view_sites')))

    if request.method == 'POST':
        vals = request.form.to_dict()
        if verify_exists(vals, ['id']):
            Asset.add_source_to_asset(asset_id, vals['id'])
            return redirect(url_for('view_asset', site_id=site_id, incident_id=incident_id, asset_id=asset_id))
        else:
            return render_template('add_source.html', message='Missing Parameter')
    else:
        source_list = Source.get_source_from_site_not_match_asset(site_id, asset_id)
        return render_template('add_source.html', source_list=source_list)

@app.route('/site/<site_id>/incident/<incident_id>/asset/<asset_id>/new_source/', methods=['GET', 'POST'])
def new_source(site_id, incident_id, asset_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return make_response(redirect(url_for('view_sites')))

    if request.method == 'POST':
        vals = request.form.to_dict()
        new_source_resp = handle_new_source(site_id, verify[1], asset_id, vals)
        if not new_source_resp[0]:
            return new_source_resp[1]
        Source.insert_user_to_incident_source(verify[1], incident_id, new_source_resp[1], new_source_resp[2])
        return redirect(url_for('view_asset', site_id=site_id, incident_id=incident_id, asset_id=asset_id))
    else:
        return render_template('new_source.html')

def generate_route_view_source_message(site_id, user_id, incident_id, asset_id, source_id, i_message):
    source_info = Source.get_info_from_id(source_id)[0] # name, location, type, magnitude
    creation_time = time.ctime(source_info[9])
    last_updated = time.ctime(source_info[10])
    asset_name = Asset.get_info_from_id(asset_id)[0]
    is_manager = Site.check_site_manager(user_id, site_id)
    locked = Source.get_user_locked_incident_source(user_id, incident_id, source_id)
    return render_template('incident_source.html', source_info=source_info, asset_name=asset_name, locked=locked, is_manager=is_manager, message=i_message, creation_time=creation_time, last_updated=last_updated)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/site/<site_id>/incident/<incident_id>/asset/<asset_id>/source/<source_id>/', methods=['GET', 'POST'], strict_slashes=False)
def view_source(site_id, incident_id, asset_id, source_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))

    if request.method == 'POST':
        vals = request.form.to_dict()
        if Site.check_site_manager(verify[1], site_id):
            if verify_exists(vals, ['action']):
                if vals['action'] == 'Delete Source':
                    Source.delete_source(source_id, verify[1])
                    return redirect(url_for('view_asset', site_id=site_id, incident_id=incident_id, asset_id=asset_id))
                elif vals['action'] == 'Remove Source from Asset':
                    Source.remove_source_from_asset(source_id, asset_id, verify[1])
                    return redirect(url_for('view_asset', site_id=site_id, incident_id=incident_id, asset_id=asset_id))

        if verify_exists(vals, ['toggle_lock']):
            if vals['toggle_lock'] == 'unlock':
                Source.update_user_locked(verify[1], incident_id, source_id, 0)
                return generate_route_view_source_message(site_id, verify[1], incident_id, asset_id, source_id, "")
            elif vals['toggle_lock'] == 'lock':
                Source.update_user_locked(verify[1], incident_id, source_id, 1)
                return generate_route_view_source_message(site_id, verify[1], incident_id, asset_id, source_id, "")
            else:
                return generate_route_view_source_message(site_id, verify[1], incident_id, asset_id, source_id, "Invalid Request")

        if 'file' not in request.files:
            return generate_route_view_source_message(site_id, verify[1], incident_id, asset_id, source_id, "No File Part")
        file = request.files['file']
        if file.filename == '':
            return generate_route_view_source_message(site_id, verify[1], incident_id, asset_id, source_id, "No File Selected")
        print(file.filename)
        print(allowed_file(file.filename))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_instance = File.File(file, app.config['UPLOAD_FOLDER'], site_id, incident_id, verify[1], source_id)
            return redirect(url_for('view_file', site_id=site_id, incident_id=incident_id, asset_id=asset_id, source_id=source_id, file_id=file_instance.id))
        return redirect(request.url)
    else:
        source_info = Source.get_info_from_id(source_id)[0] # name, location, type, magnitude
        creation_time = time.ctime(source_info[9])
        last_updated = time.ctime(source_info[10])
        asset_name = Asset.get_info_from_id(asset_id)[0]
        is_manager = Site.check_site_manager(verify[1], site_id)
        locked = Source.get_user_locked_incident_source(verify[1], incident_id, source_id)
        return render_template('incident_source.html', source_info=source_info, asset_name=asset_name, locked=locked, is_manager=is_manager, creation_time=creation_time, last_updated=last_updated)

@app.route('/site/<site_id>/incident/<incident_id>/asset/<asset_id>/source/<source_id>/view_files/', methods=['GET'], strict_slashes=False)
def view_files(site_id, incident_id, asset_id, source_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))
    
    files_list = File.get_files_by_ids(site_id, incident_id, verify[1], source_id)
    mod_files_list = []
    for file_tup in files_list:
        mod_files_list.append((file_tup[0], time.ctime(file_tup[2])))
    return render_template('view_files.html', files_list=mod_files_list)

@app.route('/site/<site_id>/source/<source_id>/', methods=['GET', 'POST'], strict_slashes=False)
def base_source(site_id, source_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))

    if request.method == 'POST':
        vals = request.form.to_dict()
        if Site.check_site_manager(verify[1], site_id):
            if verify_exists(vals, ['action']):
                if vals['action'] == 'Delete Source':
                    Source.delete_source(source_id, verify[1])
                    return redirect(url_for('view_locked_sources', site_id=site_id))
    
    source_info = Source.get_info_from_id(source_id)[0] # name, location, type, magnitude, locked
    creation_time = time.ctime(source_info[9])
    last_updated = time.ctime(source_info[10])
    is_manager = Site.check_site_manager(verify[1], site_id)
    site_name = Site.get_info_from_id(source_info[5])[0]
    users_list = Source.get_users_status_from_source_ignore_resolved(source_id)
    users_list.sort()
    users_list = list(users_list for users_list,_ in itertools.groupby(users_list))
    return render_template('source.html', source_info=source_info, users_list=users_list, site_name=site_name, is_manager=is_manager, creation_time=creation_time, last_updated=last_updated)

@app.route('/site/<site_id>/incident/<incident_id>/asset/<asset_id>/source/<source_id>/file/<file_id>/', methods=['GET'], strict_slashes=False)
def view_file(site_id, incident_id, asset_id, source_id, file_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))

    fpath, f_user_id, f_site_id, f_incident_id, f_source_id, unix_time = File.get_info_by_id(file_id)[0]
    tstring = time.ctime(unix_time)
    source_name = Source.get_info_from_id(source_id)[0][0]
    fpath_filt = fpath.replace('.', '')
    return render_template('image.html', user_image=fpath_filt, time_string=tstring, source_name=source_name, fileid=file_id)

@app.route('/uploads/<site_id>/<incident_id>/<asset_id>/<source_id>/<file_id>/', strict_slashes=False)
def serve_file(site_id, incident_id, asset_id, source_id, file_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))
        
    fpath, f_user_id, f_site_id, f_incident_id, f_source_id, unix_time = File.get_info_by_id(file_id)[0]
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f_site_id, f_incident_id, f_user_id, f_source_id)
    return send_from_directory(filepath,
                               file_id)

@app.route('/site/<site_id>/view_users/', methods=['GET'], strict_slashes=False)
def view_users(site_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))
    
    user_list = User.get_users_info_from_site(site_id)
    return render_template('view_users.html', user_info_list=user_list)

@app.route('/site/<site_id>/<path:filepath>/user/<user_id>/', methods=['GET', 'POST'], strict_slashes=False)
def show_user(site_id, filepath, user_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))

    if not Site.check_valid_site_user(user_id, site_id):
        return "INVALID USER"
        
    if request.method == 'POST':
        vals = request.form.to_dict()
        if Site.check_site_manager(verify[1], site_id):
            if not Site.check_site_manager(user_id, site_id):
                if verify_exists(vals, ['action']):
                    if vals['action'] == 'Remove User':
                        Site.remove_user(user_id, site_id, verify[1])
                    if vals['action'] == "Make User Manager":
                        Site.make_manager(user_id, site_id)
        is_user_manager = Site.check_site_manager(user_id, site_id)
        user_info = User.get_info_from_id(user_id)[0]
        is_manager = Site.check_site_manager(verify[1], site_id)
        return render_template('user.html', info=user_info, is_manager=is_manager, user_id=user_id, is_user_manager=is_user_manager, message="Invalid Operation")
    is_user_manager = Site.check_site_manager(user_id, site_id)
    user_info = User.get_info_from_id(user_id)[0]
    is_manager = Site.check_site_manager(verify[1], site_id)
    return render_template('user.html', info=user_info, is_manager=is_manager, user_id=user_id, is_user_manager=is_user_manager)

@app.route('/site/<site_id>/asset/<asset_id>/source/<source_id>/', methods=['GET', 'POST'], strict_slashes=False)
def asset_source(site_id, asset_id, source_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))

    if request.method == 'POST':
        vals = request.form.to_dict()
        if Site.check_site_manager(verify[1], site_id):
            if verify_exists(vals, ['action']):
                if vals['action'] == 'Delete Source':
                    Source.delete_source(source_id, verify[1])
                    return redirect(url_for('view_locked_sources', site_id=site_id))
                if vals['action'] == 'Remove Source from Asset':
                    Source.remove_source_from_asset(source_id, asset_id, verify[1])
    
    source_info = Source.get_info_from_id(source_id)[0] # name, location, type, magnitude, locked
    creation_time = time.ctime(source_info[9])
    last_updated = time.ctime(source_info[10])
    is_manager = Site.check_site_manager(verify[1], site_id)
    site_name = Site.get_info_from_id(source_info[5])[0]
    users_list = Source.get_users_status_from_source_ignore_resolved(source_id)
    return render_template('asset_source.html', source_info=source_info, users_list=users_list, site_name=site_name, is_manager=is_manager, creation_time=creation_time, last_updated=last_updated)

@app.route('/site/<site_id>/source/<source_id>/startup/', methods=['GET'], strict_slashes=False, defaults={'filepath': None})
@app.route('/site/<site_id>/<path:filepath>/source/<source_id>/startup/', methods=['GET'], strict_slashes=False)
def source_startup(site_id, filepath, source_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))
    
    startup_ins = Source.get_info_from_id(source_id)[0][7]
    return render_template('display_text.html', purpose="Startup Instructions", data=startup_ins)

@app.route('/site/<site_id>/source/<source_id>/shutoff/', methods=['GET'], strict_slashes=False, defaults={'filepath': None})
@app.route('/site/<site_id>/<path:filepath>/source/<source_id>/shutoff/', methods=['GET'], strict_slashes=False)
def source_shutdown(site_id, filepath, source_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))
    
    shutoff_ins = Source.get_info_from_id(source_id)[0][6]
    return render_template('display_text.html', purpose="Shutoff Instructions", data=shutoff_ins)

@app.route('/site/<site_id>/source/<source_id>/verification/', methods=['GET'], strict_slashes=False, defaults={'filepath': None})
@app.route('/site/<site_id>/<path:filepath>/source/<source_id>/verification/', methods=['GET'], strict_slashes=False)
def source_verification(site_id, filepath, source_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))

    verif_ins = Source.get_info_from_id(source_id)[0][8]
    return render_template('display_text.html', purpose="Verification Instructions", data=verif_ins)

@app.route('/site/<site_id>/asset/<asset_id>/startup/', methods=['GET'], strict_slashes=False, defaults={'filepath': None})
@app.route('/site/<site_id>/<path:filepath>/asset/<asset_id>/startup/', methods=['GET'], strict_slashes=False)
def asset_startup(site_id, filepath, asset_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))
    
    startup_ins = Asset.get_info_from_id(asset_id)[5]
    return render_template('display_text.html', purpose="Startup Instructions", data=startup_ins)

@app.route('/site/<site_id>/asset/<asset_id>/shutoff/', methods=['GET'], strict_slashes=False, defaults={'filepath': None})
@app.route('/site/<site_id>/<path:filepath>/asset/<asset_id>/shutoff/', methods=['GET'], strict_slashes=False)
def asset_shutdown(site_id, filepath, asset_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))
    
    shutoff_ins = Asset.get_info_from_id(asset_id)[6]
    return render_template('display_text.html', purpose="Shutoff Instructions", data=shutoff_ins)

@app.route('/site/<site_id>/asset/<asset_id>/verification/', methods=['GET'], strict_slashes=False, defaults={'filepath': None})
@app.route('/site/<site_id>/<path:filepath>/asset/<asset_id>/verification/', methods=['GET'], strict_slashes=False)
def asset_verification(site_id, filepath, asset_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))

    verif_ins = Asset.get_info_from_id(asset_id)[7]
    return render_template('display_text.html', purpose="Verification Instructions", data=verif_ins)

@app.route('/site/<site_id>/asset/<asset_id>/edit_asset/', methods=['GET', 'POST'], strict_slashes=False, defaults={'filepath': None})
@app.route('/site/<site_id>/<path:filepath>/asset/<asset_id>/edit_asset/', methods=['GET', 'POST'], strict_slashes=False)
def edit_asset(site_id, filepath, asset_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))

    if request.method == 'POST':
        vals = request.form.to_dict()
        if verify_exists(vals, ['name', 'location', 'manu', 'model_num', 'serial_num', 'shutoff_ins', 'startup_ins', 'verif_ins']):
            Asset.update_by_id(asset_id, vals['name'], vals['location'], vals['manu'], vals['model_num'], vals['serial_num'],
            vals['shutoff_ins'], vals['startup_ins'], vals['verif_ins'])
            return redirect(request.url.replace('edit_asset/', '').replace('edit_asset', ''))
        else:
            asset_info = Asset.get_info_from_id(asset_id)
        return render_template('edit_asset.html', data=asset_info, message="Missing Parameter")

    asset_info = Asset.get_info_from_id(asset_id)
    return render_template('edit_asset.html', data=asset_info)

@app.route('/site/<site_id>/source/<source_id>/edit_source/', methods=['GET', 'POST'], strict_slashes=False, defaults={'filepath': None})
@app.route('/site/<site_id>/<path:filepath>/source/<source_id>/edit_source/', methods=['GET', 'POST'], strict_slashes=False)
def edit_source(site_id, filepath, source_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))

    if request.method == 'POST':
        vals = request.form.to_dict()
        if not verify_exists(vals, ['name', 'location', 'type', 'shutoff_ins', 'startup_ins', 'verif_ins']):
            source_info = Source.get_info_from_id(source_id)
            return render_template('edit_source.html', data=source_info, message='Missing Parameter')
        if 'magnitude' not in vals:
            vals['magnitude'] = ''
        vals['private'] = 0 if 'private' not in vals else 1
        Source.update_by_id(source_id, vals['name'], vals['location'], vals['type'], vals['magnitude'], vals['shutoff_ins'], vals['startup_ins'], vals['verif_ins'], vals['private'])
        request.url.replace('edit_source/', '').replace('edit_source', '')

    source_info = Source.get_info_from_id(source_id)[0]
    return render_template('edit_source.html', data=source_info)

@app.route('/site/<site_id>/view_no_file_list/', methods=['GET'], strict_slashes=False)
def view_no_file_list(site_id):
    verify = User.validate_token(request.cookies.get('token'))
    if not verify[0]:
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('token', '', expires=0)
        return resp
    
    if not Site.check_valid_site_user(verify[1], site_id):
        return redirect(url_for('view_sites'))

    no_file_list = File.incident_source_with_no_file(site_id)
    processed_list = []
    for no_file in no_file_list:
        print(no_file)
        user_info = (no_file[0], *User.get_info_from_id(no_file[0])[0])
        incident_info = (no_file[1], *Incident.get_info_from_id(no_file[1])[0])
        incident_info = (*incident_info, time.ctime(incident_info[2]))
        asset_info = (no_file[2], *Asset.get_info_from_id(no_file[2]))
        source_info = (no_file[3], *Source.get_info_from_id(no_file[3])[0])
        processed_list.append((user_info, incident_info, asset_info, source_info))

    processed_list.sort(key=lambda x: x[1][2], reverse=True)
        
    return render_template('view_no_file.html', no_file_list=processed_list)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory(app.static_folder, os.path.join('css', path))

