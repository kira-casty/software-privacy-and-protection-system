from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify, Blueprint
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
import bcrypt
import pymysql
import requests
import base64
from datetime import datetime
import json
from views import views
from dotenv import load_dotenv
import os
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
from scripts.database_setup import setup_database
import logging



load_dotenv()

app = Flask(__name__)
mail = Mail(app)
app.secret_key = os.getenv('SECRET_KEY')
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True


app.register_blueprint(views,url_prefix='/')

setup_database()
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    app.run(debug=True)
