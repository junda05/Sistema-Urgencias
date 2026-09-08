import pymysql
import configparser
import os

class AuthenticationModel:
    credentials = {
        'user': '',
        'workstation': ''
    }

    @staticmethod
    def set_server(host):
        AuthenticationModel.credentials['workstation'] = host

    @staticmethod
    def get_credentials():
        return AuthenticationModel.credentials

    @staticmethod
    def clear_credentials():
        AuthenticationModel.credentials = {
            'user': '',
            'workstation': ''
        }

    @staticmethod
    def validate_credentials(user, password):
        """Validates the user's credentials against the database"""
        try:
            config = configparser.ConfigParser()
            config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
            db_config = config['DATABASE']

            conn = pymysql.connect(
                host=db_config['host'],
                user=user,
                password=password,
                db=db_config['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )

            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

            conn.close()

            if result:
                AuthenticationModel.credentials['user'] = user
                return True, "Valid credentials"
            else:
                return False, "Invalid credentials"

        except pymysql.err.OperationalError as e:
            return False, str(e)

        except Exception as e:
            return False, str(e)