from flask import Blueprint, render_template, jsonify, request, flash, send_from_directory, flash, redirect, url_for
from flask_jwt_extended import jwt_required, current_user, unset_jwt_cookies, set_access_cookies
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from .. import db
from ..models.user import User
from ..models.administrator import Administrator
from ..models.employer import Employer
from ..models.student import Student

from.index import index_views

from App.controllers import (
    login
)

auth = Blueprint('auth_views', __name__, template_folder='../templates')   
    
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        user_type = request.form.get('user_type')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('auth_views.signup'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('auth_views.signup'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('auth_views.signup'))

        user_classes = {
            'student': Student,
            'admin': Administrator,
            'employer': Employer
        }

        UserClass = user_classes.get(user_type)
        if not UserClass:
            flash('Invalid user type!', 'error')
            return redirect(url_for('auth_views.signup'))

        new_user = UserClass(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth_views.login_action'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration.', 'error')
            return redirect(url_for('auth_views.signup'))

    return render_template('Html/signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login_action():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            print(f"Logged in user type: {user.user_type}") 
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard_views.dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('Html/login.html')

@auth.route('/logout')
@login_required
def logout_action():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@auth.route('/api/login', methods=['POST'])
def user_login_api():
  data = request.json
  token = login(data['username'], data['password'])
  if not token:
    return jsonify(message='bad username or password given'), 401
  response = jsonify(access_token=token) 
  set_access_cookies(response, token)
  return response

@auth.route('/api/identify', methods=['GET'])
@jwt_required()
def identify_user():
    return jsonify({'message': f"username: {current_user.username}, id : {current_user.id}"})

@auth.route('/api/logout', methods=['GET'])
def logout_api():
    response = jsonify(message="Logged Out!")
    unset_jwt_cookies(response)
    return response

def init_auth_routes(app):
    app.register_blueprint(auth)