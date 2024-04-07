from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify, Blueprint
import bcrypt
import requests
import base64
from datetime import datetime
import json
from forms import RegisterForm, LoginForm, ForgotPasswordForm, ForgotPasswordForm, ResetPasswordForm
from utils.utils import get_access_token, initiate_stk_push ,connect_to_database, generate_reset_token,send_reset_email
import requests, uuid, json
import random
import os
import time
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer
from flask import request, current_app as app, url_for
import logging
import subprocess
from werkzeug.utils import secure_filename


load_dotenv()
tag = os.getenv('TAG')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


views = Blueprint("views",__name__)

@views.route('/threat')
def run_streamlit():
    subprocess.run(["streamlit", "run", "./stride-gpt/main.py"])
    return "threat model is running..."

@views.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html', title='License.io | Not Found'), 404

@views.route('/')
def index():
    get_access_token()
    return render_template('home.html', title='License.io | Home')

@views.route('/pricing')
def pricing():
    return render_template('pricing.html', title='License.io | Pricing')

@views.route('/about')
def about():
    return render_template('about.html', title='License.io | About')

@views.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = connect_to_database()
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
            conn.commit()
        except Exception as e:
            conn.rollback()
            flash("An error occurred while registering: {}".format(str(e)), 'error')
            return redirect(url_for('views.register'))
        finally:
            cur.close()
            conn.close()

        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('views.login'))

    return render_template('register.html', form=form, title='License.io | Register')


@views.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        with connect_to_database().cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cur.fetchone()

            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                session['user_id'] = user['id']
                if user['is_super_user']:
                    return redirect(url_for('views.admin'))
                else:
                    flash("You have logged in successfully.")
                    return redirect(url_for('views.dashboard'))
            else:
                flash("Login failed. Please check your email and password")
                return redirect(url_for('views.login'))

    return render_template('login.html', form=form, title='License.io | Login')

@views.route('/admin')
def admin():
    if 'user_id' in session:
        user_id = session['user_id']
        connection = connect_to_database()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                
                if user:
                    user_name = user['name']
                    cursor.execute("SELECT COUNT(*) FROM users WHERE is_super_user = 0")
                    registered_users_count = cursor.fetchone()['COUNT(*)']
                    
                    cursor.execute("SELECT SUM(Amount) FROM transaction")
                    total_amount = cursor.fetchone()['SUM(Amount)']
                    
                    return render_template('adminpanel.html', user=user, user_name=user_name, title='License.io | Admin', registered_users_count=registered_users_count, total_amount=total_amount)
        finally:
            connection.close()
            
    return redirect(url_for('views.login'))


    
@views.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']

        with connect_to_database().cursor() as cur:
            cur.execute("SELECT * FROM users where id=%s", (user_id,))
            user = cur.fetchone()

        if user:
            user_name = user['name']
            return render_template('dashboard.html', user=user, user_name=user_name,title='License.io | Dashboard')

    return redirect(url_for('login'))


@views.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out successfully.")
    return redirect(url_for('views.index'))


@views.route("/initiate", methods=['POST'])
def initiate():
    phone_number = request.json.get('phone')
    result = initiate_stk_push(phone_number) 
    if 'error' in result:
        return jsonify({'error': result['error']}), 500 
    else:
        return jsonify({'[itskios-09]': 'STK push initiated successfully', 'CheckoutRequestID': result['CheckoutRequestID']}), 200 
    
@views.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        connection = connect_to_database()
        try:
            with connection.cursor() as cursor:
                sql_check_email = "SELECT * FROM users WHERE email=%s"
                cursor.execute(sql_check_email, (email,))
                user = cursor.fetchone()
                if user:
                    token = generate_reset_token(email)
                    send_reset_email(email, token)
                    flash('Password reset link has been sent to your email')
                else:
                    flash('Email does not exist')
        finally:
            connection.close()
        
        return redirect(url_for('views.forgot_password'))

    return render_template('forgot_password.html', form=form, title='License.io | Forgot Password')



@views.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'], max_age=3600)
    except:
        flash('The reset link is invalid or has expired')
        return redirect(url_for('views.forgot_password'))  
    
    form = ResetPasswordForm()  
    if form.validate_on_submit():
        new_password = form.password.data
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        connection = connect_to_database()
        try:
            with connection.cursor() as cursor:
                sql_check_email = "SELECT * FROM users WHERE email=%s"
                cursor.execute(sql_check_email, (email,))
                user = cursor.fetchone()
                if user:
                    sql_update_password = "UPDATE users SET password=%s WHERE email=%s"
                    cursor.execute(sql_update_password, (hashed_password.decode('utf-8'), email))
                    connection.commit()
                    flash('Your password has been updated')
                    return redirect(url_for('views.login'))  
                else:
                    flash('Email does not exist')
                    return redirect(url_for('views.forgot_password'))  
        finally:
            connection.close()
    
    return render_template('reset_password.html', form=form, title='License.io | Reset Password', token=token)

@views.route('/verify', methods=['POST'])
def verify_receipt():
    connection = connect_to_database()
    try:
        data = request.json
        mpesa_receipt_number = data.get('mpesa_receipt_number', '').upper() 
        with connection.cursor() as cursor:
            sql_check_receipt = "SELECT * FROM transaction WHERE MpesaReceiptNumber = %s AND is_verified = 1"
            cursor.execute(sql_check_receipt, (mpesa_receipt_number,))
            receipt = cursor.fetchone()
            if receipt:
                response = jsonify({'message': 'M-Pesa receipt number already verified'})
                logging.info(f'{tag}: M-Pesa receipt number already verified: %s', response.json)
                return response, 200
            else:
                sql_update_receipt = "UPDATE transaction SET is_verified = 1 WHERE MpesaReceiptNumber = %s"
                cursor.execute(sql_update_receipt, (mpesa_receipt_number,))
                connection.commit()
                affected_rows = cursor.rowcount
                if affected_rows > 0:
                    response = jsonify({'message': 'M-Pesa receipt number verified successfully'})
                    logging.info(f'{tag}: M-Pesa receipt number verified successfully: %s', response.json)
                    return response, 200
                else:
                    response = jsonify({'message': 'Kindly make payment first'})
                    logging.info(f'{tag}: Receipt not found: %s', response.json)
                    return response, 404
    except Exception as e:
        response = jsonify({'message': str(e)})
        logging.error('Error verifying receipt: %s', response.json)
        return response, 500
    finally:
        connection.close()
        
@views.route('/process_request', methods=['POST'])
def process_request():
    connection = connect_to_database()
    mpesa_receipt = request.form['mpesa'].upper()
    selected_api_from_ui = request.form.get('selected_api')

    if not selected_api_from_ui:
        return jsonify({'status': 'error', 'message': 'No API key selected'})

    api_key_mapping = {
        'OpenAI key': 'LLM',
    }
    selected_api_from_db = api_key_mapping.get(selected_api_from_ui)

    if selected_api_from_db is None:
        return jsonify({'status': 'error', 'message': 'Invalid API key selection'})

    cursor = connection.cursor()

    cursor.execute('SELECT * FROM transaction WHERE MpesaReceiptNumber = %s', (mpesa_receipt,))
    mpesa_row = cursor.fetchone()

    if not mpesa_row:
        return jsonify({'status': 'error', 'message': 'Mpesa receipt number does not exist'})

    is_verified = mpesa_row['is_verified']
    if is_verified != 1:
        return jsonify({'status': 'error', 'message': 'Please verify your M-Pesa receipt'})

    cursor.execute('SELECT apikey FROM apikeys WHERE Type = %s', (selected_api_from_db,))
    api_key = cursor.fetchone()

    if not api_key:
        return jsonify({'status': 'error', 'message': 'API key not found'})

    api_data = {'api_key': api_key['apikey']}
    cursor.close()
    connection.close()

    return jsonify({'status': 'success', 'data': api_data})
