from flask import jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User

def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    user_id = User.create(data['username'], data['password'])
    if user_id is None:
        return jsonify({'error': 'Username already exists'}), 409
    
    access_token = create_access_token(identity=str(user_id))
    return jsonify({'access_token': access_token, 'user_id': user_id}), 201

def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    user = User.verify_password(data['username'], data['password'])
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=str(user['id']))
    return jsonify({'access_token': access_token, 'user_id': user['id']}), 200

def get_current_user_id():
    return int(get_jwt_identity())
