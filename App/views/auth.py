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

        try:
            if user_type == 'student':
                student_id = f"STU{username.upper()}"
                new_user = Student(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    student_id=student_id
                )
            elif user_type == 'admin':
                new_user = Administrator(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
            elif user_type == 'employer':
                new_user = Employer(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    user_type='employer' 
                )
                print(f"Creating employer user: {username}")  
            else:
                flash('Invalid user type!', 'error')
                return redirect(url_for('auth_views.signup'))
            
            print(f"Creating new user with type: {user_type}") 
            
            db.session.add(new_user)
            db.session.commit()
            
            # Verify the user type after creation
            created_user = User.query.filter_by(username=username).first()
            print(f"Created user type: {created_user.user_type}") 
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth_views.login'))
        except Exception as e:
            print(f"Error during signup: {str(e)}") 
            db.session.rollback()
            flash('An error occurred during registration.', 'error')
            return redirect(url_for('auth_views.signup'))

    return render_template('Html/signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            
            # Redirect based on user type
            if user.user_type == 'student':
                return redirect(url_for('dashboard_views.student_profile'))
            elif user.user_type == 'admin':
                return redirect(url_for('dashboard_views.admin_dashboard'))
            elif user.user_type == 'employer':
                return redirect(url_for('dashboard_views.search_candidates'))
            
            # Fallback to main dashboard if user type is not recognized
            return redirect(url_for('dashboard_views.dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('Html/login.html')

@auth.route('/logout')
@login_required
def logout_action():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth_views.login'))

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