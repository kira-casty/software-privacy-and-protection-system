import logging
import pymysql
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()
tag = os.getenv('TAG')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_database():
    try:

        connection = pymysql.connect(
            host=os.getenv('DATABASE_HOST'),
            user=os.getenv('DATABASE_USERNAME'),
            password=os.getenv('DATABASE_PASSWORD')
        )

        with connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS db")
            cursor.execute("USE db")

            cursor.execute("SHOW TABLES LIKE 'users'")
            users_table_exists = cursor.fetchone()

            if users_table_exists:
                logging.info(f'{tag}: Table "users" already exists')
            else:
                cursor.execute("""
                    CREATE TABLE users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100) NOT NULL,
                        password VARCHAR(100) NOT NULL,
                        is_super_user BOOLEAN DEFAULT 0
                    )
                """)
                logging.info(f'{tag}: Table "users" created')

            cursor.execute("SHOW TABLES LIKE 'apikeys'")
            apikeys_table_exists = cursor.fetchone()

            if apikeys_table_exists:
                logging.info(f'{tag}: Table "apikeys" already exists')
            else:
                cursor.execute("""
                    CREATE TABLE apikeys (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        Type VARCHAR(100) NOT NULL,
                        apikey VARCHAR(100) NOT NULL,
                        `usage` BOOLEAN DEFAULT 0
                    )
                """)
                logging.info(f'{tag}: Table "apikeys" created')

                default_apikeys = [
                    ('LLM', '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', False),
                    ('RNN', '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', False),
                    ('RASA', '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', False)
                ]
                cursor.executemany("""
                    INSERT INTO apikeys (Type, apikey, `usage`) 
                    VALUES (%s, %s, %s)
                """, default_apikeys)
                logging.info(f'{tag}: Default API keys inserted')

            cursor.execute("SHOW TABLES LIKE 'transaction'")
            transaction_table_exists = cursor.fetchone()

            if transaction_table_exists:
                logging.info(f'{tag}: Table "transaction" already exists')
            else:
                cursor.execute("""
                    CREATE TABLE transaction (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        TransactionDate DATETIME,
                        MpesaReceiptNumber VARCHAR(255),
                        PhoneNumber VARCHAR(255),
                        Amount DECIMAL(10, 2),
                        CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_verified BOOLEAN DEFAULT 0,
                        rate_limit BOOLEAN DEFAULT 0
                    )
                """)
            logging.info(f'{tag}: Table "transaction" created')


            cursor.execute("SELECT * FROM users WHERE email = 'admin@admin.io'")
            existing_user = cursor.fetchone()

            if existing_user:
                logging.info(f'{tag}: Superuser "admin" already exists')
            else:
                name = os.getenv('SUPERUSER_NAME')
                email = os.getenv('SUPERUSER_EMAIL')
                password = os.getenv('SUPERUSER_PASSWORD')
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                admin_data = (name, email, hashed_password, True)
                cursor.execute("""
                    INSERT INTO users (name, email, password, is_super_user) 
                    VALUES (%s, %s, %s, %s)
                """, admin_data)
                logging.info(f'{tag}: Superuser "admin" created')

        connection.commit()
        connection.close()
        logging.info(f'{tag}: Database setup script execution completed')
    except pymysql.MySQLError as e:
        logging.error(f'{tag}: MySQL error during database setup: {str(e)}')
    except Exception as e:
        logging.error(f'{tag}: Error during database setup: {str(e)}')
        raise
