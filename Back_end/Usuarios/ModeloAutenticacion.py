import pymysql
import configparser
import os

class ModeloAutenticacion:
    credenciales = {
        'usuario': '',
        'equipo_trabajo': ''
    }

    @staticmethod
    def establecer_servidor(host):
        ModeloAutenticacion.credenciales['equipo_trabajo'] = host

    @staticmethod
    def obtener_credenciales():
        return ModeloAutenticacion.credenciales

    @staticmethod
    def limpiar_credenciales():
        ModeloAutenticacion.credenciales = {
            'usuario': '',
            'equipo_trabajo': ''
        }

    @staticmethod
    def validar_credenciales(usuario, contrasena):
        """Valida las credenciales del usuario contra la base de datos"""
        try:
            config = configparser.ConfigParser()
            config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
            db_config = config['DATABASE']

            conn = pymysql.connect(
                host=db_config['host'],
                user=usuario,
                password=contrasena,
                db=db_config['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )

            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

            conn.close()

            if result:
                ModeloAutenticacion.credenciales['usuario'] = usuario
                return True, "Credenciales válidas"
            else:
                return False, "Credenciales inválidas"

        except pymysql.err.OperationalError as e:
            return False, str(e)

        except Exception as e:
            return False, str(e)