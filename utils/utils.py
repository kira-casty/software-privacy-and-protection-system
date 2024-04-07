import requests
from dotenv import load_dotenv
import os
import pymysql
from flask import request
import requests, uuid, json
import time
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
from flask import request, current_app as app, url_for
from flask_mail import Mail, Message
import logging
from datetime import datetime
import base64
import string
import random





load_dotenv()
tag = os.getenv('TAG')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def connect_to_database():
    try:
        connection = pymysql.connect(
            host=os.getenv('DATABASE_HOST'),
            user=os.getenv('DATABASE_USERNAME'),
            password=os.getenv('DATABASE_PASSWORD'),
            database=os.getenv('DATABASE_NAME'),
            cursorclass=pymysql.cursors.DictCursor
        )
        
        logging.info(f'{tag}: Database connected successfully')
        return connection
    except Exception as e:
        logging.error(f'{tag}: Error connecting to database: {str(e)}')
        raise
    

def get_access_token():
    consumer_key = os.getenv('CONSUMER_KEY')
    consumer_secret = os.getenv('CONSUMER_SECRET') 
    access_token_url = os.getenv('ACCESS_TOKEN_URL')
    headers = {'Content-Type': 'application/json'}
    auth = (consumer_key, consumer_secret)
        
    try:
        response = requests.get(access_token_url, headers=headers, auth=auth)
        response.raise_for_status() 
        result = response.json()
        access_token = result['access_token']
        logging.info(f'{tag}: Getting access token: {access_token}')
            
        return access_token
    except requests.exceptions.RequestException as e:
        return str(e)

def initiate_stk_push(phone_number):
    access_token = get_access_token()
    logging.info(f"{tag}: Access Token in initiate_stk_push: {access_token}")    
    endpoint = os.getenv('STK_PUSH_URL')
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer %s" % access_token   
    }
    Timestamp = datetime.now()
    times = Timestamp.strftime("%Y%m%d%H%M%S")
    businessShortCode = os.getenv('BUSINESS_SHORTCODE')
    passkey = os.getenv('PASSKEY')
    password = businessShortCode + passkey + times
    datapass = base64.b64encode(password.encode('utf-8')).decode('utf-8')  

    data = {
        "BusinessShortCode": businessShortCode,
        "Password": datapass,
        "Timestamp": times,
        "TransactionType": "CustomerPayBillOnline",
        "PartyA": phone_number, 
        "PartyB": businessShortCode,
        "PhoneNumber": phone_number,
        "CallBackURL": "http://www.kj.com",
        "AccountReference": "Mtafsiri.io",
        "TransactionDesc": "API Payment",
        "Amount": 1
        }

    res = requests.post(endpoint, json = data, headers = headers)
    logging.info(f"{tag}: Getting data: {res.json()}")
    return res.json()


def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

def send_reset_email(email, token):
    mail = Mail(app)
    reset_link = url_for('views.reset_password', token=token, _external=True)
    msg = Message('Password Reset Request', sender=os.getenv('SENDER'), recipients=[email])
    msg.body = f"Click the following link to reset your password: {reset_link}"
    mail.send(msg)  


