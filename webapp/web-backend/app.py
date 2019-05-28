from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import authenticate_user as my_auth
import uuid
import jwt
import datetime
import os
import requests
import json
app = Flask(__name__)

app.config['SECRET_KEY'] = 'pucsdrocks'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(80))
    mount_point = db.Column(db.String(150))
    #admin = db.Column(db.Boolean)

def update_user(public_id):
    
    user = User.query.filter_by(public_id=public_id).first()
    user.public_id = str(uuid.uuid4())
    db.session.commit()
    return {'message': 'Your are logged out!'}

def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
            if not current_user:
                return jsonify({'message' : 'Token is invalid!'}), 401
        except:
                return jsonify({'message' : 'Token is invalid!'}), 401

        return func(current_user, *args, **kwargs)
    return decorated

@app.route('/api/login', methods=['GET'])
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
   
    user = User.query.filter_by(name=auth.username).first()
    
    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
    
    is_valid_user =  my_auth.authenticate_user(auth.username, auth.password)

    if is_valid_user:
        mount_path = '192.168.43.5:/zfs-storage/students/' + user.name 
       # p_id = os.fork()
       # exit_code = 0
       # if p_id == 0: 
       #     exit_code = os.execv('/bin/mount',['mount', '-t', 'nfs', mount_path, user.mount_point])
        os.system('mount -t nfs '+ mount_path + ' '+ user.mount_point)
        print("Mounted user directory")
       # if exit_code != 0:
       #      return jsonify({"message": "Error while mounting user directory!!"}), 500
        uuid1 = str(uuid.uuid4())
        token = jwt.encode({"public_id": user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes = 20)}, app.config['SECRET_KEY'])
        return jsonify({'token': token.decode('UTF-8')}), 200
    
    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

@app.route('/api/get-directory-contents')
@token_required
def get_directory_contents(current_user):
    path = current_user.mount_point
    return jsonify({"ls_contents": os.listdir(path)}), 200

@app.route('/api/create-file', methods = ['POST'])
@token_required
def create_file(current_user):
    file_path = request.json.get('file_path')
    path = current_user.mount_point + file_path
    if os.path.exists(path):
        return jsonify({'message': 'File already exist!'}), 422
    f = open(path, 'w')
    f.close()
    return jsonify({'message': 'File created'}), 201

@app.route('/api/delete-file', methods = ['POST'])
@token_required
def delete_file(current_user):
    file_path = request.json.get('file_path')
    path = current_user.mount_point + file_path
    #access_path = os.path.dirname(path)
    if not os.path.exists(path):
        return jsonify({'message': 'File does not exist!'}), 422
    os.system('rm '+ path)
    return jsonify({'message': 'Deleted file successfully'}), 201


@app.route('/api/save-file', methods=['POST'])
@token_required
def save_file(current_user):
    file_path = request.json.get('file_path')
    path = current_user.mount_point + file_path
    content = request.json.get('data')
    path = current_user.mount_point + file_path
    f = open(path, 'w')
    f.write(content)
    f.close()
    return jsonify({'message': 'Saved!'}), 201


@app.route('/api/create-job', methods=['POST'])
@token_required
def create_job(current_user):
    file_path = request.json.get('file_path')
    job_tool = request.json.get('job_tool')
    if not file_path or not job_tool: 
        return jsonify({'message': 'Invalid data!!!'}), 400
    response =  requests.post('http://192.168.43.5:5000/create_job', json = {"file_path": file_path, "user": current_user.name, "job_tool": job_tool })
    if response.status_code != 200:
        return jsonify({'message': 'error occured while creation of jobs'}), 500
    json_data = response.json()
    output_dir = current_user.mount_point + "/.jobs/"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    os.mkdir(output_dir + json_data['jobID'])
    f1 = open(output_dir + json_data['jobID'] + '/' + json_data["jobID"], 'w')
    json_data["file_path"]=file_path
    f1.write(str(json_data))
    f1.close()
    f = open(current_user.mount_point+'/.jobs/jobs_index', 'a')
    f.write(json_data["jobID"] + ' : ' + file_path + ' : ' + json_data["created_at"])
    f.close()
    return jsonify(response.json())


@app.route('/api/tools', methods=['GET'])
@token_required
def get_tools(current_user):
    response = requests.get('http://192.168.43.5:5000/tools')
    #json_data = json.loads(response.text)
    json_data = response.json()
    return jsonify(json_data), 200

@app.route('/api/jobs', methods=['GET'])
@token_required
def get_jobs(current_user):
    job_path = current_user.mount_point + '/.jobs/'
    if not os.path.exists(job_path):
         return jsonify({'message': 'There are no any job created yet!!!'}), 200
    jobs = []
    with open(job_path + "job_index") as fp:
        line = fp.readline()
        cnt = 1
        l = line.split(':')
        jobs.append({"jobID": l[0], "file_path": l[1], "created_at": l[2]})
    return jsonify(jobs), 200

       


@app.route('/api/status/<jobID>', methods=['GET'])
@token_required
def get_status(current_user, jobID):
    job_path = current_user.mount_point + '/.jobs/' + jobID
    if not os.path.exists(job_path):
         return jsonify({'message': 'Invalid jobID'}), 400
    f = open(job_path + '/'+ jobID, 'r')
    st = f.read()
    ls = st.split(' ')
    return jsonify({"status": ls[0], "at_time": ls[1] + ' ' + ls[2] }), 200
@app.route('/api/logout')
@token_required
def logout(current_user):
    token = request.headers['x-access-token']
    data = jwt.decode(token, app.config['SECRET_KEY'])
    print(data['public_id'])
   # p_id = os.fork()
   # exit_code = 0
   # if p_id == 0:
   #     exit_code = os.execv('/bin/umount', [current_user.mount_point])
   # if exit_code != 0:
   #      return jsonify({'message': 'Error while umounting user directory!!'}), 500
    os.system('umount ' + current_user.mount_point)
    return jsonify(update_user(data['public_id'])), 200

if __name__ == '__main__':
    app.run(debug=True)
