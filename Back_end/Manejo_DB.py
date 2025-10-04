import pymysql
from unidecode import unidecode
from datetime import datetime
import re
from PyQt5.QtCore import pyqtSignal, QObject
import os
import sys
import configparser
import json 

# Colores para estados de pacientes
COLORES = {
    # Para Triaje, CI y RV
    "Realizado": "#69DD45",  # Verde
    "No realizado": "#FF0000",  # Rojo
    "1": "#69DD45",  # Verde
    "2": "#69DD45",  # Verde
    "3": "#69DD45",  # Verde
    "4": "#69DD45",  # Verde
    "5": "#69DD45",  # Verde 

    # Para Labs e IX
    "No se ha realizado": "#FF0000",  # Rojo
    "En espera de resultados": "#FFD900",  # Amarillo 
    "Resultados completos": "#69DD45",  # Verde 
    
    # Para Interconsulta
    "No se ha abierto": "#FF0000",  # Rojo 
    "Abierta": "#FFD900",  # Amarillo 
    "Realizada": "#69DD45"  # Verde 
}

class ModeloConfiguracion:
    """Modelo para gestionar la configuración de la aplicación"""
    
    @staticmethod
    def get_config_path():
        """Determina la ruta del archivo de configuración"""
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        config_path = os.path.join(base_path, 'config.ini')
        print(f"Config file path: {config_path}")
        return config_path
    
    @classmethod
    def cargar_configuracion(cls):
        """Carga la configuración desde el archivo config.ini"""
        try:
            config_path = cls.get_config_path()
            
            if not os.path.exists(config_path):
                cls.crear_archivo_config(config_path)
            
            # Leer la configuración
            config = configparser.ConfigParser()
            config.read(config_path)
            
            # Retornar el host de la base de datos
            return config.get('DATABASE', 'host', fallback='localhost')
            
        except Exception as e:
            print(f"Error al cargar configuración: {str(e)}")
            return 'localhost'  # Valor por defecto en caso de error
    
    @staticmethod
    def crear_archivo_config(config_path):
        """Crea un archivo de configuración con valores predeterminados"""
        try:
            config = configparser.ConfigParser()
            config['DATABASE'] = {'host': 'localhost'}
            
            # Añadir sección ADMIN con credenciales por defecto
            config['ADMIN'] = {
                'user': 'Urgencias_1',
                'password': 'Josma@0409'
            }
            
            # Añadir sección DBA_USERS para usuarios con privilegios de administración
            config['DBA_USERS'] = {'users': 'Urgencias_1'}
            
            with open(config_path, 'w') as config_file:
                config.write(config_file)
            
            return True
        except Exception as e:
            print(f"Error al crear archivo de configuración: {str(e)}")
            return False

    @classmethod
    def guardar_configuracion(cls, nuevo_host):
        """Guarda la configuración en el archivo config.ini"""
        try:
            config_path = cls.get_config_path()
            config = configparser.ConfigParser()
            
            # Si el archivo existe, cargar la configuración actual
            if os.path.exists(config_path):
                config.read(config_path)
            
            # Asegurar que exista la sección DATABASE
            if 'DATABASE' not in config:
                config['DATABASE'] = {}
            
            # Actualizar el host
            config['DATABASE']['host'] = nuevo_host
            
            # Guardar la configuración
            with open(config_path, 'w') as archivo_config:
                config.write(archivo_config)
                
            return True, ""
        except Exception as e:
            return False, str(e)


class ModeloAutenticacion:
    """Modelo para gestionar la autenticación de usuarios"""
    
    _credenciales = {'usuario': None, 'contrasena': None, 'equipo_trabajo': None}
    
    @classmethod
    def obtener_credenciales(cls):
        """Retorna las credenciales actuales"""
        return cls._credenciales.copy()
    
    @classmethod
    def establecer_servidor(cls, servidor):
        """Establece el servidor en las credenciales"""
        cls._credenciales['equipo_trabajo'] = servidor
    
    @classmethod
    def validar_credenciales(cls, usuario, contrasena):
        """Valida las credenciales del usuario intentando conectar a la base de datos"""
        from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
        
        if not usuario or not contrasena:
            return False, "Por favor complete todos los campos antes de continuar."
            
        # Validar que el usuario y contraseña cumplan con los requisitos de formato
        if not ModeloUsuarios.validar_nombre_usuario(usuario):
            return False, "El nombre de usuario no es válido."
        
        try:
            conexion = pymysql.connect(
                host=cls._credenciales['equipo_trabajo'], 
                user=usuario, 
                password=contrasena, 
                database='sistema_visualizacion'
            )
            conexion.close()

            # Guardar credenciales válidas
            cls._credenciales['usuario'] = usuario
            cls._credenciales['contrasena'] = contrasena
            
            return True, "Credenciales válidas"
            
        except pymysql.Error as e:
            return False, f"Error al intentar conectarse: {str(e)}\nPor favor, verifique los datos ingresados."
    
    @classmethod
    def limpiar_credenciales(cls):
        """Limpia las credenciales de usuario y contraseña"""
        cls._credenciales['usuario'] = None
        cls._credenciales['contrasena'] = None
    
    @classmethod
    def verificar_rol_admin(cls, username=None):
        """
        Verifica si un usuario tiene rol de administrador
        
        Args:
            username: Nombre de usuario a verificar (o el usuario actual si es None)
            
        Returns:
            bool: True si tiene rol de administrador, False en caso contrario
        """
        from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
        
        if username is None and cls._credenciales['usuario'] is not None:
            username = cls._credenciales['usuario']
        
        if not username:
            return False
            
        return ModeloUsuarios.obtener_rol_usuario(username) == 'admin'


class ModeloPaciente(QObject):
    datos_actualizados = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.conn = None

    @staticmethod
    def conectar():
        credenciales = ModeloAutenticacion.obtener_credenciales()
        return pymysql.connect(
            host=credenciales['equipo_trabajo'], 
            user=credenciales['usuario'], 
            password=credenciales['contrasena'], 
            database='sistema_visualizacion'
        )
        
        # return pymysql.connect(
        #     host=credenciales['equipo_trabajo'], 
        #     user=credenciales['usuario'], 
        #     password=credenciales['contrasena'], 
        #     database='sistema_visualizacion'
        # )

    def organizar_por_ingreso(self):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nombre, documento, triage, ci, labs, ix, inter, rv, pendientes, 
                conducta, ubicacion, ingreso, triage_timestamp, id, observacion_timestamp 
            FROM pacientes 
            ORDER BY ingreso DESC
        """)
        datos = cursor.fetchall()
        conn.close()
        return datos

    def obtener_registro_por_documento(self, documento):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pacientes WHERE documento = %s", (documento,))
        pacientes = cursor.fetchall()
        conn.close()
        return pacientes
    
    def buscar_pacientes(self, termino_busqueda):
        """
        Busca pacientes por nombre o documento que contengan el término de búsqueda
        
        Args:
            termino_busqueda: Término a buscar en nombre o documento
            
        Returns:
            list: Lista de pacientes que coinciden con el criterio
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            
            # Buscar pacientes que contengan el término en nombre o documento
            query = """
                SELECT nombre, documento, ubicacion, id, ingreso
                FROM pacientes
                WHERE LOWER(nombre) LIKE %s OR LOWER(documento) LIKE %s
                ORDER BY ingreso DESC
                LIMIT 20
            """
            
            parametro = f"%{termino_busqueda.lower()}%"
            cursor.execute(query, (parametro, parametro))
            resultados = cursor.fetchall()
            conn.close()
            
            return resultados
        except Exception as e:
            print(f"Error al buscar pacientes: {str(e)}")
            return []
    
    def verificar_paciente_mismo_documento(self, documento):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM pacientes WHERE documento = %s", (documento,))
        paciente_existente_doc = cursor.fetchone()
        return paciente_existente_doc
    
    def insertar_en_db(self, datos, ubicacion):
        # Validar el nombre antes de insertar
        validacion_nombre = self.validar_nombre(datos['nombre'])
        if validacion_nombre:
            return False, validacion_nombre
        
        # Validar el documento si no es paciente NN
        if not datos['nombre'].startswith('NN -'):
            if not datos.get('documento'):
                return False, "El documento es obligatorio para pacientes no anónimos"
        
        conn = self.conectar()
        cursor = conn.cursor()
        
        # Determinar timestamp según triage
        triage = datos.get('triage', '')
        triage_timestamp = datetime.now() if triage in ["1", "2", "3", "4", "5"] else None
        
        # Determinar timestamp de observación
        observacion_timestamp = datos.get('observacion_timestamp')
        
        sql = """INSERT INTO pacientes (nombre, documento, triage, triage_timestamp, ci, labs, 
                    ix, inter, rv, pendientes, conducta, ubicacion, ingreso, observacion_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)"""
        valores = (
            datos['nombre'], datos.get('documento', ''), triage, 
            triage_timestamp, 
            datos.get('ci', '') or "", datos.get('labs', '') or "", 
            datos.get('ix', '') or "", datos.get('inter', '') or "",
            datos.get('rv', '') or "", datos.get('pendientes', ''),
            datos.get('conducta', '') or "", ubicacion,
            observacion_timestamp
        )
        cursor.execute(sql, valores)
        # Obtener el ID del paciente recién insertado
        paciente_id = cursor.lastrowid
        conn.commit()
        
        # Registrar en la trazabilidad
        # Crear detalles de cambios para la trazabilidad
        detalles = []
        if datos.get('documento'):
            detalles.append(f"Documento: {datos.get('documento')}")
        if datos.get('triage'):
            detalles.append(f"TRIAGE: {datos.get('triage')}")
        if datos.get('ci'):
            detalles.append(f"CI: {datos.get('ci')}")
        if datos.get('labs'):
            detalles.append(f"LABS: {datos.get('labs')}")
        if datos.get('ix'):
            detalles.append(f"IMG: {datos.get('ix')}")
        if datos.get('inter'):
            detalles.append(f"INTER: {datos.get('inter')}")
        if datos.get('rv'):
            detalles.append(f"RV: {datos.get('rv')}")
        if datos.get('conducta'):
            detalles.append(f"CONDUCTA: {datos.get('conducta')}")
        if datos.get('pendientes'):
            detalles.append(f"PENDIENTES: {datos.get('pendientes')}")
        
        # Añadir ubicación a los detalles
        detalles.append(f"UBICACIÓN: {ubicacion}")
        
        # Registrar acción en la trazabilidad
        ModeloTrazabilidad.registrar_accion(
            accion="Agregar paciente",
            paciente_afectado=datos['nombre'],
            detalles_cambio=" | ".join(detalles)
        )
        
        self.datos_actualizados.emit()
        return True, "Paciente guardado correctamente", paciente_id
    
    def verificar_paciente_mismo_nombre_diferente_documento(self):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT documento, nombre FROM pacientes")
        todos_pacientes = cursor.fetchall()
        return todos_pacientes
    
    def datos_actualizar_paciente(self, datos, ubicacion, registro):
        # Validar el nombre antes de actualizar
        validacion_nombre = self.validar_nombre(datos['nombre'])
        if validacion_nombre:
            return False, validacion_nombre
            
        # Validar el documento si no es paciente NN
        if not datos['nombre'].startswith('NN -'):
            if not datos.get('documento'):
                return False, "El documento es obligatorio para pacientes no anónimos"
        
        conn = self.conectar()
        cursor = conn.cursor()
        
        # Obtener información del paciente actual para el registro en consola
        cursor.execute("""
            SELECT nombre, documento, triage, ci, labs, ix, inter, rv, pendientes, conducta, triage_timestamp 
            FROM pacientes WHERE id=%s
        """, (registro[13],))
        datos_actuales = cursor.fetchone()
        
        if datos_actuales:
            nombre_paciente = datos_actuales[0]
            documento_paciente = datos_actuales[1]
            estado_previo = {
                'triage': datos_actuales[2],
                'ci': datos_actuales[3],
                'labs': datos_actuales[4],
                'ix': datos_actuales[5],
                'inter': datos_actuales[6],
                'rv': datos_actuales[7],
                'pendientes': datos_actuales[8],
                'conducta': datos_actuales[9]
            }
            triage_timestamp_previo = datos_actuales[10]
            
            # Imprimir información de seguimiento
            print(f"\n[ACTUALIZANDO PACIENTE] - {nombre_paciente} ({documento_paciente})")
            print(f"ID: {registro[13]}")
            
            # Mostrar cambios en los estados principales
            print("Cambios de estado:")
            
            # Construir detalles de cambios para trazabilidad
            detalles_cambios = []
            for campo in ['triage', 'ci', 'labs', 'ix', 'inter', 'rv', 'conducta']:
                estado_anterior = estado_previo[campo]
                estado_nuevo = datos.get(campo, '')
                if estado_anterior != estado_nuevo:
                    print(f"  - {campo.upper()}: {estado_anterior or 'vacío'} → {estado_nuevo or 'vacío'}")
                    detalles_cambios.append(f"{campo.upper()}: {estado_anterior or 'vacío'} → {estado_nuevo or 'vacío'}")
            
            # Verificar si hay cambios en pendientes
            pendientes_anteriores = estado_previo['pendientes'] or ''
            pendientes_nuevos = datos.get('pendientes', '') or ''
            if pendientes_anteriores != pendientes_nuevos:
                detalles_cambios.append(f"PENDIENTES: '{pendientes_anteriores}' → '{pendientes_nuevos}'")
            
            # Mostrar cambios en pendientes si hay
            print(f"Pendientes anteriores: {estado_previo['pendientes'] or 'Ninguno'}")
            print(f"Pendientes actualizados: {datos.get('pendientes', '') or 'Ninguno'}")
            
            # Si hay cambios, registrar en la trazabilidad
            if detalles_cambios:
                detalle_texto = " | ".join(detalles_cambios)
                ModeloTrazabilidad.registrar_accion(
                    accion="Editar paciente",
                    paciente_afectado=nombre_paciente,
                    detalles_cambio=detalle_texto
                )
        
        # Determinar timestamp según triage
        triage_actual = estado_previo.get('triage', '')
        triage_nuevo = datos.get('triage', '')
        
        # Lógica mejorada para el timestamp de triage
        triage_timestamp = None
        
        # Caso 1: Si el triage nuevo es válido (1-5)
        if triage_nuevo in ["1", "2", "3", "4", "5"]:
            # Si cambia de un triage válido a otro triage válido diferente, actualizar timestamp
            if triage_actual in ["1", "2", "3", "4", "5"] and triage_actual != triage_nuevo:
                print(f"Actualizando timestamp de triage: cambio de {triage_actual} a {triage_nuevo}")
                triage_timestamp = datetime.now()
            # Si viene desde un estado no válido a un triage válido, establecer timestamp
            elif triage_actual not in ["1", "2", "3", "4", "5"]:
                print(f"Estableciendo timestamp de triage inicial para valor {triage_nuevo}")
                triage_timestamp = datetime.now()
            # Si no cambia, mantener el timestamp existente
            else:
                triage_timestamp = triage_timestamp_previo
        # Caso 2: Si se cambia a "No realizado" o valor no válido, anular el timestamp
        else:
            triage_timestamp = None
            print("Anulando timestamp de triage por cambio a valor no válido")
        
        # Verificar si el estado de conducta cambió a Observación
        observacion_timestamp = None
        if datos.get('conducta') == 'Observación':
            # Consultar si el registro anterior ya estaba en Observación
            cursor.execute("SELECT conducta, observacion_timestamp FROM pacientes WHERE id=%s", (registro[13],))
            resultado = cursor.fetchone()
            if resultado:
                conducta_anterior, timestamp_anterior = resultado
                # Si ya estaba en Observación, mantener el timestamp original
                if conducta_anterior == 'Observación' and timestamp_anterior:
                    observacion_timestamp = timestamp_anterior
                else:
                    # Si es nuevo en Observación, crear timestamp ahora
                    observacion_timestamp = datetime.now()
        
        sql = """UPDATE pacientes SET nombre=%s, triage=%s, triage_timestamp=%s, ci=%s, labs=%s, 
                    ix=%s, inter=%s, rv=%s, pendientes=%s, conducta=%s, ubicacion=%s, observacion_timestamp=%s 
                    WHERE id=%s"""
        valores = (
            datos['nombre'], triage_nuevo, triage_timestamp,
            datos.get('ci', '') or "", datos.get('labs', '') or "", 
            datos.get('ix', '') or "", datos.get('inter', '') or "", 
            datos.get('rv', '') or "", datos.get('pendientes', ''),
            datos.get('conducta', '') or "", ubicacion, observacion_timestamp,
            registro[13]  # ID ahora en índice 13
        )
        cursor.execute(sql, valores)
        conn.commit()
        
        # Calcular y almacenar métricas para el paciente actualizado
        paciente_id = registro[13]
        try:
            # Calcular y almacenar métricas sólo para este paciente actualizado
            ModeloTrazabilidad.calcular_y_almacenar_metricas(paciente_id)
            print(f"✅ Métricas actualizadas para el paciente ID {paciente_id}")
        except Exception as e:
            print(f"⚠️ Error al actualizar métricas para el paciente ID {paciente_id}: {str(e)}")
        
        self.datos_actualizados.emit()
        print("✅ Paciente actualizado correctamente")
        return True, "Paciente actualizado correctamente"
    
    def actualizar_timestamp(self, paciente_id, campo_timestamp):
        """
        Actualiza un timestamp específico para un paciente
        
        Args:
            paciente_id (int): ID del paciente
            campo_timestamp (str): Nombre del campo timestamp a actualizar
        
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        try:
            conn = self.conectar()
            if not conn:
                return False
                
            cursor = conn.cursor()
            timestamp_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Validar que el campo timestamp exista
            campos_validos = [
                'triage_timestamp', 
                'ci_no_realizado_timestamp', 'ci_realizado_timestamp',
                'labs_no_realizado_timestamp', 'labs_solicitados_timestamp', 'labs_completos_timestamp',
                'ix_no_realizado_timestamp', 'ix_solicitados_timestamp', 'ix_completos_timestamp',
                'inter_no_abierta_timestamp', 'inter_abierta_timestamp', 'inter_realizada_timestamp',
                'rv_no_realizado_timestamp', 'rv_realizado_timestamp', 
                'observacion_timestamp', 'alta_timestamp'
            ]
            
            if campo_timestamp not in campos_validos:
                print(f"Campo timestamp no válido: {campo_timestamp}")
                return False
            
            query = f"""
                UPDATE pacientes
                SET {campo_timestamp} = %s
                WHERE id = %s
            """
            
            cursor.execute(query, (timestamp_actual, paciente_id))
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error al actualizar timestamp: {str(e)}")
            return False
        finally:
            if conn and hasattr(conn, 'close'):
                cursor.close()
                conn.close()

    def actualizar_estado_con_timestamp(self, paciente_id, campo_estado, nuevo_estado, campo_timestamp=None):
        """
        Actualiza un estado y su timestamp asociado
        
        Args:
            paciente_id (int): ID del paciente
            campo_estado (str): Nombre del campo de estado a actualizar
            nuevo_estado (str): Nuevo valor para el estado
            campo_timestamp (str, opcional): Nombre del campo timestamp a actualizar.
                Si no se especifica, se infiere del campo_estado
        
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        try:
            conn = self.conectar()
            if not conn:
                return False
                
            cursor = conn.cursor()
            timestamp_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Si es actualización de triage, verificar valor actual y nuevo valor
            if campo_estado == 'triage':
                # Solo para valores válidos de triage (1-5)
                if nuevo_estado in ["1", "2", "3", "4", "5"]:
                    # Obtener el valor actual del triage
                    cursor.execute("SELECT triage FROM pacientes WHERE id = %s", (paciente_id,))
                    triage_actual_resultado = cursor.fetchone()
                    triage_actual = triage_actual_resultado[0] if triage_actual_resultado else None
                    
                    # Si se está cambiando de un triage válido a otro, actualizar el timestamp
                    if triage_actual in ["1", "2", "3", "4", "5"] and triage_actual != nuevo_estado:
                        print(f"Actualizando timestamp de triage para paciente {paciente_id}: cambio de {triage_actual} a {nuevo_estado}")
                        query = f"""
                            UPDATE pacientes
                            SET {campo_estado} = %s, triage_timestamp = %s
                            WHERE id = %s
                        """
                        cursor.execute(query, (nuevo_estado, timestamp_actual, paciente_id))
                        conn.commit()
                        
                        # Calcular y almacenar métricas inmediatamente
                        ModeloTrazabilidad.calcular_y_almacenar_metricas(paciente_id)
                        return True
                    
                    # Si es la primera vez o viene de "No realizado", establecer timestamp
                    if not triage_actual or triage_actual not in ["1", "2", "3", "4", "5"]:
                        print(f"Estableciendo nuevo timestamp de triage para paciente {paciente_id}")
                        query = f"""
                            UPDATE pacientes
                            SET {campo_estado} = %s, triage_timestamp = %s
                            WHERE id = %s
                        """
                        cursor.execute(query, (nuevo_estado, timestamp_actual, paciente_id))
                        conn.commit()
                        
                        # Calcular y almacenar métricas inmediatamente
                        ModeloTrazabilidad.calcular_y_almacenar_metricas(paciente_id)
                        return True
                    
                    # Si no cambió el valor, solo actualizar el triage sin cambiar el timestamp
                    query = f"""
                        UPDATE pacientes
                        SET {campo_estado} = %s
                        WHERE id = %s
                    """
                    cursor.execute(query, (nuevo_estado, paciente_id))
                    conn.commit()
                    
                    # Calcular y almacenar métricas inmediatamente
                    ModeloTrazabilidad.calcular_y_almacenar_metricas(paciente_id)
                    return True
                else:
                    # Si es "No realizado" u otro valor no válido, solo actualizar el estado sin timestamp
                    query = f"""
                        UPDATE pacientes
                        SET {campo_estado} = %s, triage_timestamp = NULL
                        WHERE id = %s
                    """
                    cursor.execute(query, (nuevo_estado, paciente_id))
                    conn.commit()
                    
                    # Calcular y almacenar métricas inmediatamente
                    ModeloTrazabilidad.calcular_y_almacenar_metricas(paciente_id)
                    return True
            
            # Inferir campo timestamp si no se proporciona
            if not campo_timestamp:
                # Mapeo de estados a campos timestamp correspondientes
                mapa_estado_timestamp = {
                    'triage': {
                        '1': 'triage_timestamp',
                        '2': 'triage_timestamp',
                        '3': 'triage_timestamp',
                        '4': 'triage_timestamp',
                        '5': 'triage_timestamp'
                    },
                    'ci': {
                        'No realizado': 'ci_no_realizado_timestamp',
                        'Realizado': 'ci_realizado_timestamp'
                    },
                    'labs': {
                        'No se ha realizado': 'labs_no_realizado_timestamp',
                        'En espera de resultados': 'labs_solicitados_timestamp',
                        'Resultados completos': 'labs_completos_timestamp'
                    },
                    'ix': {
                        'No se ha realizado': 'ix_no_realizado_timestamp',
                        'En espera de resultados': 'ix_solicitados_timestamp',
                        'Resultados completos': 'ix_completos_timestamp'
                    },
                    'inter': {
                        'No se ha abierto': 'inter_no_abierta_timestamp',
                        'Abierta': 'inter_abierta_timestamp',
                        'Realizada': 'inter_realizada_timestamp'
                    },
                    'rv': {
                        'No realizado': 'rv_no_realizado_timestamp',
                        'Realizado': 'rv_realizado_timestamp'
                    },
                    'conducta': {
                        'Observación': 'observacion_timestamp',
                        'De Alta': 'alta_timestamp'
                    }
                }
                
                # Determinar el campo timestamp basado en el campo de estado y el nuevo valor
                if campo_estado in mapa_estado_timestamp:
                    if isinstance(mapa_estado_timestamp[campo_estado], dict):
                        # Si es un diccionario, buscar el campo específico para el nuevo estado
                        if nuevo_estado in mapa_estado_timestamp[campo_estado]:
                            campo_timestamp = mapa_estado_timestamp[campo_estado][nuevo_estado]
                        else:
                            print(f"No se encontró campo timestamp para estado '{campo_estado}' con valor '{nuevo_estado}'")
                            # En lugar de fallar, solo actualizar el estado sin timestamp
                            query = f"""
                                UPDATE pacientes
                                SET {campo_estado} = %s
                                WHERE id = %s
                            """
                            cursor.execute(query, (nuevo_estado, paciente_id))
                            conn.commit()
                            return True
                    else:
                        # Si es un valor directo, usarlo
                        campo_timestamp = mapa_estado_timestamp[campo_estado]
            
            if not campo_timestamp:
                print(f"No se pudo inferir el campo timestamp para el estado: {campo_estado} = {nuevo_estado}")
                # En lugar de fallar, actualizar solo el estado
                query = f"""
                    UPDATE pacientes
                    SET {campo_estado} = %s
                    WHERE id = %s
                """
                cursor.execute(query, (nuevo_estado, paciente_id))
                conn.commit()
                return True
            
            # Actualizar el estado y el timestamp
            query = f"""
                UPDATE pacientes
                SET {campo_estado} = %s, {campo_timestamp} = %s
                WHERE id = %s
            """
            
            cursor.execute(query, (nuevo_estado, timestamp_actual, paciente_id))
            conn.commit()
            
            # Calcular y almacenar métricas inmediatamente
            ModeloTrazabilidad.calcular_y_almacenar_metricas(paciente_id)
            
            return True
            
        except Exception as e:
            print(f"Error al actualizar estado con timestamp: {str(e)}")
            return False
        finally:
            if conn and hasattr(conn, 'close'):
                cursor.close()
                conn.close()

    def validar_nombre(self, nombre):
        """
        Valida que el nombre cumpla con las reglas establecidas:
        - No puede estar vacío
        - Si no es NN, debe tener al menos 3 palabras
        
        Returns:
            None si es válido, mensaje de error si no lo es
        """
        if not nombre.strip():
            return "El nombre del paciente es obligatorio"
            
        # Verificar si es un paciente NN
        if nombre.startswith('NN -'):
            return None  # Los pacientes NN son un caso especial y se permiten
        
        # Contar palabras en el nombre
        palabras = nombre.strip().split()
        
        if len(palabras) < 3:
            return "El nombre debe tener al menos tres palabras (nombres y apellidos)"
            
        return None  # Nombre válido

    def procesar_nombre(self, nombre):
        """
        Procesa el nombre para estandarizarlo:
        - Elimina espacios extras
        - Elimina tildes
        - Capitaliza cada palabra
        - Si está vacío o tiene una sola palabra, sugiere registrarlo como NN
        
        Returns:
            tuple: (nombre_procesado, es_anonimo, mensaje)
                - nombre_procesado: el nombre ya procesado
                - es_anonimo: True si debe ser registrado como NN
                - mensaje: mensaje informativo o None
        """
        nombre = nombre.strip() if nombre else ""
        
        # Si está vacío, sugerir registrar como anónimo
        if not nombre:
            return nombre, True, "El nombre está vacío. Se registrará como anónimo (NN)"
            
        palabras = re.split(r'\s+', nombre)  # Dividir por cualquier espacio en blanco
        
        if len(palabras) == 1:
            # Si solo hay una palabra, sugerir registrar como anónimo
            return nombre, True, "El nombre solo tiene una palabra. Se sugiere registrarlo como anónimo (NN)"
            
        # Eliminar tildes y capitalizar cada palabra correctamente
        nombre_normalizado = ' '.join(palabra.capitalize() for palabra in [unidecode(p) for p in palabras])
        
        return nombre_normalizado, False, None

    def crear_nombre_nn(self):
        """Crea un nombre para paciente anónimo con la fecha y hora actual"""
        fecha_hora_actual = datetime.now().strftime("%Y-%m-%d - %H:%M:%S")
        return f"NN - {fecha_hora_actual}"

    @staticmethod
    def normalizar_texto(texto):
        """Normaliza un texto para formato estándar"""
        from unidecode import unidecode
        if not texto:
            return texto
            
        texto_normalizado = unidecode(texto.lower())
        return ' '.join(palabra.capitalize() for palabra in texto_normalizado.split())

    @staticmethod
    def comparar_nombres(nombre1, nombre2):
        """Compara dos nombres eliminando espacios, tildes y convirtiendo a minúsculas"""
        if not nombre1 or not nombre2:
            return False
            
        nombre1 = unidecode(nombre1.lower().replace(" ", ""))
        nombre2 = unidecode(nombre2.lower().replace(" ", ""))
        return nombre1 == nombre2

    def eliminar(self, id_registro):
        conn = self.conectar()
        cursor = conn.cursor()
        
        # Obtener información del paciente antes de eliminarlo para la trazabilidad
        cursor.execute("SELECT nombre, documento FROM pacientes WHERE id = %s", (id_registro,))
        paciente_info = cursor.fetchone()
        
        if paciente_info:
            nombre_paciente = paciente_info[0]
            documento_paciente = paciente_info[1]
            
            # Eliminar el paciente
            sql = "DELETE FROM pacientes WHERE id = %s"
            cursor.execute(sql, (id_registro,))
            conn.commit()
            
            # Registrar en la trazabilidad
            detalles = f"Documento: {documento_paciente}"
            ModeloTrazabilidad.registrar_accion(
                accion="Eliminar paciente",
                paciente_afectado=nombre_paciente,
                detalles_cambio=detalles
            )
            
            print(f"✅ Paciente eliminado: {nombre_paciente} ({documento_paciente})")
        else:
            # Si no se encontró el paciente, solo ejecutar la eliminación
            sql = "DELETE FROM pacientes WHERE id = %s"
            cursor.execute(sql, (id_registro,))
            conn.commit()
            print(f"✅ Registro con ID {id_registro} eliminado (no se encontró información del paciente)")
            
        cursor.close()
        conn.close()
        self.datos_actualizados.emit()

    def cierre_db(self):
        """Cierra la conexión a la base de datos si está abierta"""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                self.conn = None
        except Exception as e:
            print(f"Error al cerrar la conexión: {e}")
        
    def validar_estado_paciente(self, datos):
        """
        Valida que los estados de un paciente sean consistentes según las reglas de negocio.
        
        Reglas:
        1. CI no puede estar en 'Realizado' si no hay nivel de triage
        2. Interconsulta no puede estar en 'Abierta'/'Realizada' si CI/triage/labs/IMG no están realizados
        3. RV no puede estar 'Realizada' si interconsulta/labs/imágenes/CI/triage no están realizados
        4. No se puede dar de alta a un paciente si no todos los procesos están realizados/completos
        
        Args:
            datos: Diccionario con los datos del paciente
            
        Returns:
            str: Mensaje de error si hay inconsistencias, None si todo es válido
        """
        estados = {
            'triage': datos.get('triage', ''),
            'ci': datos.get('ci', ''),
            'labs': datos.get('labs', ''),
            'ix': datos.get('ix', ''),
            'inter': datos.get('inter', ''),
            'rv': datos.get('rv', ''),
            'conducta': datos.get('conducta', '')
        }

        # 1. Verificaciones basadas en Triage
        if estados['triage'] not in ["1", "2", "3", "4", "5"]:
            # CI no puede estar en 'Realizado' si no hay nivel de triage
            if estados['ci'] == 'Realizado':
                return "CI no puede estar en 'Realizado' si no se ha establecido el nivel de triage."
                
            # Ningún otro proceso puede avanzar si no hay triage
            campos_restringidos = ['labs', 'ix', 'inter', 'rv']
            for campo in campos_restringidos:
                if estados[campo] in ['Resultados completos', 'Abierta', 'Realizada', 'Realizado', 'En espera de resultados']:
                    return f"Los demás procesos no pueden tener estados si el triage no está realizado. Error en {campo.upper()}."

        # 2. Verificaciones basadas en CI
        if estados['ci'] != 'Realizado':
            campos_restringidos = ['labs', 'ix', 'inter', 'rv']
            for campo in campos_restringidos:
                if estados[campo] in ['Resultados completos', 'Abierta', 'Realizada', 'Realizado', 'En espera de resultados']:
                    return f"El procedimiento no puede estar en curso o realizado porque CI no está culminado. Error en {campo.upper()}."

        # 3. Verificaciones basadas en Interconsulta
        if estados['inter'] in ['Abierta', 'Realizada']:
            # Verificar que CI y triage estén realizados
            if estados['triage'] not in ["1", "2", "3", "4", "5"]:
                return "Interconsulta no puede estar 'Abierta' o 'Realizada' si no se ha establecido el nivel de triage."
            if estados['ci'] != 'Realizado':
                return "Interconsulta no puede estar 'Abierta' o 'Realizada' si CI no está realizado."
            # Verificar que al menos un examen (labs o imágenes) esté en proceso o completado
            if (estados['labs'] != 'Resultados completos' and 
                estados['ix'] != 'Resultados completos'):
                # estados['ix'] not in ['En espera de resultados', 'Resultados completos'])
                return "Interconsulta no puede estar 'Abierta' o 'Realizada' si no se ha realizado al menos un examen (Labs o IMG)."

        # 4. Verificaciones basadas en RV
        if estados['rv'] == 'Realizado':
            # Para RV, verificar que todos los procesos previos estén realizados
            if estados['triage'] not in ["1", "2", "3", "4", "5"]:
                return "RV no puede estar 'Realizado' si no se ha establecido el nivel de triage."
            if estados['ci'] != 'Realizado':
                return "RV no puede estar 'Realizado' si CI no está realizado."
            if estados['inter'] != 'Realizada':
                return "RV no puede estar 'Realizado' si Interconsulta no está realizada."
            # Verificar que al menos un examen esté completo
            if (estados['labs'] != 'Resultados completos' and 
                estados['ix'] != 'Resultados completos'):
                return "RV no puede estar 'Realizado' si no se han completado al menos un examen (Labs o IMG)."

        # 5. Verificación para estado "De Alta"
        if estados['conducta'] == 'De Alta':
            # Verificar triage y CI
            if estados['triage'] not in ["1", "2", "3", "4", "5"]:
                return "No se puede dar de alta al paciente si no se ha establecido el nivel de triage."
            if estados['ci'] != 'Realizado':
                return "No se puede dar de alta al paciente si CI no está realizado."
                
            # Verificar que interconsulta esté realizada
            if estados['inter'] == 'No se ha abierto':
                return "No se puede dar de alta al paciente si no se ha abierto una interconsulta."
            elif estados['inter'] == 'Abierta':
                return "No se puede dar de alta al paciente si la interconsulta está abierta pero no realizada."
                
            # Verificar que RV esté realizado
            if estados['rv'] != 'Realizado':
                return "No se puede dar de alta al paciente si RV no está realizado."
                
            # Verificar que al menos un tipo de examen esté con resultados completos
            if estados['labs'] != 'Resultados completos' and estados['ix'] != 'Resultados completos':
                return "No se puede dar de alta al paciente sin tener al menos un resultado completo (Labs o IMG)."
                
            # Verificar que ni labs ni imágenes estén en estados intermedios
            if estados['labs'] == 'En espera de resultados':
                return "No se puede dar de alta al paciente mientras Labs está en espera de resultados."
            if estados['ix'] == 'En espera de resultados':
                return "No se puede dar de alta al paciente mientras IMG está en espera de resultados."

        # Si todas las validaciones pasan
        return None
    
    def verificar_alarmas(self, datos):
        """
        Verifica las condiciones de alarma para los pacientes.
        Retorna un conjunto de tuplas (row_idx, col_idx) que representan las celdas con alarma.
        
        Args:
            datos: Lista de registros de pacientes
            
        Returns:
            set: Conjunto de tuplas (row_idx, col_idx) con las celdas que deben tener alarma
        """
        alarm_cells = set()
        
        for row_idx, fila in enumerate(datos):
            triage = fila[2]  # Índice de triage
            ci = fila[3]      # Índice de ci
            triage_timestamp = fila[12]  # Índice del timestamp de triage
            
            # Verificar condiciones de alarma
            if triage in ['2', '3'] and ci == 'No realizado' and triage_timestamp:
                ahora = datetime.now()
                if isinstance(triage_timestamp, datetime):
                    tiempo_transcurrido = (ahora - triage_timestamp).total_seconds()
                    
                    # Alarma para triage 2: más de 15 minutos sin CI
                    # Alarma para triage 3: más de 30 minutos sin CI
                    if (triage == '2' and tiempo_transcurrido >= 5) or \
                       (triage == '3' and tiempo_transcurrido >= 10):
                        ci_col = 3  # Índice de la columna CI
                        alarm_cells.add((row_idx, ci_col))
        
        return alarm_cells

    def verificar_alarma_conducta(self, datos):
        """
        Verifica las condiciones de alarma para pacientes en estado de Observación.
        Retorna un conjunto de tuplas (row_idx, col_idx) que representan las celdas con alarma.
        
        Args:
            datos: Lista de registros de pacientes
            
        Returns:
            set: Conjunto de tuplas (row_idx, col_idx) con las celdas que deben tener alarma
        """
        conducta_alarm_cells = set()
        
        for row_idx, fila in enumerate(datos):
            conducta = fila[9]       # Índice de conducta
            observacion_timestamp = None   # Timestamp específico para observación
            
            # Verificar si tenemos el campo observacion_timestamp en los datos
            if len(fila) > 14: 
                observacion_timestamp = fila[14]
            
            # Verificar condiciones de alarma para conducta
            if conducta == "Observación" and observacion_timestamp:
                ahora = datetime.now()
                if isinstance(observacion_timestamp, datetime):
                    # Para pruebas: 20 segundos
                    # En producción: 11 horas (39600 segundos)
                    tiempo_limite_segundos = 20  # 20 segundos para pruebas
                    
                    tiempo_transcurrido = (ahora - observacion_timestamp).total_seconds()
                    
                    if tiempo_transcurrido >= tiempo_limite_segundos:
                        conducta_col = 9  # Índice de la columna Conducta
                        conducta_alarm_cells.add((row_idx, conducta_col))
        
        return conducta_alarm_cells

    def obtener_colores(self):
        """Obtener los colores para diferentes estados, incluyendo los niveles de triage."""
        colores = {
            "1": "#663300",       # Verde para triage 1
            "2": "#660066",
            "3": "#3b82f6",
            "4": "#8b5cf6",       # Verde para triage 4
            "5": "#ec4899",       # Verde para triage 5
            "No realizado": "#CC0000",  # Rojo para triage no realizado
            "Realizado": "#00D000",     # Verde para CI realizado
            "No se ha realizado": "#CC0000",       # Rojo para labs/IMG no realizados
            "En espera de resultados": "#FFCC00",  # Amarillo para resultados pendientes
            "Resultados completos": "#00D000",     # Verde para resultados completos
            "No se ha abierto": "#CC0000",        # Rojo para interconsulta no abierta
            "Abierta": "#FFCC00",                 # Amarillo para interconsulta abierta
            "Realizada": "#00D000",               # Verde para interconsulta realizada
        }
        return colores

    def obtener_datos_pacientes_filtrados(self, areas_seleccionadas=None, fecha_inicio=None, fecha_fin=None):
        """
        Obtiene datos de pacientes filtrados por áreas específicas y/o rango de fechas.
        
        Args:
            areas_seleccionadas: Lista de áreas seleccionadas
            fecha_inicio: Fecha de inicio del rango (formato: 'YYYY-MM-DD HH:MM:SS')
            fecha_fin: Fecha de fin del rango (formato: 'YYYY-MM-DD HH:MM:SS')
            
        Returns:
            list: Lista de registros de pacientes filtrados
        """
        conn = self.conectar()
        cursor = conn.cursor()
        
        # Construir las condiciones WHERE basadas en los filtros
        condiciones = []
        
        # Filtro por áreas
        if areas_seleccionadas and len(areas_seleccionadas) > 0:
            area_conditions = []
            for area in areas_seleccionadas:
                area_conditions.append(f"ubicacion LIKE '{area}%'")
            
            if area_conditions:
                condiciones.append("(" + " OR ".join(area_conditions) + ")")
        
        # Filtro por fecha
        if fecha_inicio and fecha_fin:
            condiciones.append(f"ingreso BETWEEN '{fecha_inicio}' AND '{fecha_fin}'")
        
        query = """
            SELECT nombre, documento, triage, ci, labs, ix, inter, rv, pendientes, 
                conducta, ubicacion, ingreso, triage_timestamp, id, observacion_timestamp 
            FROM pacientes
        """
        
        # Agregar las condiciones WHERE si existen
        if condiciones:
            query += " WHERE " + " AND ".join(condiciones)
        
        # Ordenar por fecha de ingreso descendente
        query += " ORDER BY ingreso DESC"
        
        # Ejecutar la consulta
        cursor.execute(query)
        datos = cursor.fetchall()
        conn.close()
        
        return datos
    
    def datos_guardar_paciente(self, datos, ubicacion):
        """
        Método principal para guardar un nuevo paciente en la base de datos.
        Esta función valida los datos y delega la inserción al método insertar_en_db.
        
        Args:
            datos: Diccionario con los datos del paciente
            ubicacion: String con la ubicación del paciente (área - cubículo)
            
        Returns:
            tuple: (exito, mensaje) donde exito es un booleano y mensaje es un string
        """
        try:
            # Validar el nombre antes de insertar
            validacion_nombre = self.validar_nombre(datos['nombre'])
            if validacion_nombre:
                return False, validacion_nombre
                
            # Validar el estado del paciente
            validacion_estado = self.validar_estado_paciente(datos)
            if validacion_estado:
                return False, validacion_estado
                
            # Registrar timestamp de observación si corresponde
            if datos.get('conducta') == 'Observación':
                datos['observacion_timestamp'] = datetime.now()
            else:
                datos['observacion_timestamp'] = None
                
            # Insertar en la base de datos
            return self.insertar_en_db(datos, ubicacion)
        except Exception as e:
            return False, f"Error al guardar paciente: {str(e)}", None
        
    def obtener_laboratorios_paciente(self, paciente_id):
        """Obtiene los laboratorios asociados a un paciente"""
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.codigo_lab, l.nombre_lab, pl.estado 
            FROM pacientes_laboratorios pl
            JOIN laboratorios l ON pl.codigo_lab = l.codigo_lab
            WHERE pl.paciente_id = %s
        """, (paciente_id,))
        laboratorios = cursor.fetchall()
        conn.close()
        return laboratorios
        
    def guardar_laboratorios_paciente(self, paciente_id, laboratorios):
        """
        Guarda los laboratorios asociados a un paciente y actualiza los pendientes.
        Valida que haya concordancia entre el estado de Labs y los labs seleccionados.
        
        Args:
            paciente_id: ID del paciente
            laboratorios: Lista con códigos de laboratorios a guardar
            
        Returns:
            tuple: (exito, mensaje) donde exito es un booleano y mensaje es un string
        """
        # Verificar primero si triage y CI están realizados
        conn = self.conectar()
        cursor = conn.cursor()
        
        # Obtener información del paciente para el registro en consola
        cursor.execute("SELECT nombre, documento, triage, ci, labs FROM pacientes WHERE id = %s", (paciente_id,))
        resultado = cursor.fetchone()
        
        if not resultado:
            conn.close()
            return False, "No se encontró el paciente"
        
        nombre_paciente = resultado[0]
        documento_paciente = resultado[1]
        triage, ci, estado_labs = resultado[2], resultado[3], resultado[4]
        
        # Imprimir información de seguimiento
        print(f"\n[GUARDANDO LABORATORIOS] - {nombre_paciente} ({documento_paciente})")
        print(f"ID: {paciente_id}")
        print(f"Estado actual: Triage={triage}, CI={ci}, Labs={estado_labs}")
        print(f"Laboratorios a guardar: {len(laboratorios)}")
        
        # Validar que triage y CI estén realizados
        if triage not in ["1", "2", "3", "4", "5"] or ci != "Realizado":
            print(f"⚠️ Error: El triage y CI deben estar realizados antes de asociar laboratorios")
            conn.close()
            return False, "El triage y CI deben estar realizados antes de asociar laboratorios"
        
        # Validación de concordancia entre estado Labs y laboratorios seleccionados
        estados_validos = ["No se ha realizado", "En espera de resultados", "Resultados completos"]
        
        # ✅ Si hay laboratorios pero no se ha establecido un estado válido
        if laboratorios and (not estado_labs or estado_labs not in estados_validos):
            print(f"⚠️ Error: Debe establecer un estado válido en Labs cuando selecciona laboratorios")
            conn.close()
            return False, "Debe establecer un estado válido en Labs cuando selecciona laboratorios"
        
        # ✅ Si hay un estado válido pero no hay laboratorios seleccionados
        if not laboratorios and estado_labs in estados_validos:
            print(f"⚠️ Error: Ha seleccionado un estado para Labs pero no ha agregado ningún laboratorio")
            conn.close()
            return False, "Ha seleccionado un estado para Labs pero no ha agregado ningún laboratorio"
        
        # Si no hay laboratorios y no hay estado, simplemente eliminar las asociaciones antiguas
        if not laboratorios and (not estado_labs or estado_labs not in estados_validos):
            cursor.execute("DELETE FROM pacientes_laboratorios WHERE paciente_id = %s", (paciente_id,))
            # Actualizar el estado en la tabla de pacientes a vacío si tiene algún valor
            if estado_labs:
                cursor.execute("UPDATE pacientes SET labs = '' WHERE id = %s", (paciente_id,))
            conn.commit()
            conn.close()
            print("✅ No se asociaron laboratorios (eliminadas asociaciones existentes)")
            return True, "No se asociaron laboratorios"
        
        # Continuar con el procedimiento normal de inserción de laboratorios
        cursor.execute("DELETE FROM pacientes_laboratorios WHERE paciente_id = %s", (paciente_id,))
        
        # Obtener detalles de los laboratorios para mostrar en consola
        lab_detalles = []
        
        # Insertar nuevos laboratorios
        for codigo_lab in laboratorios:
            # Obtener el nombre del laboratorio para mostrar en consola
            cursor.execute("SELECT nombre_lab FROM laboratorios WHERE codigo_lab = %s", (codigo_lab,))
            lab_info = cursor.fetchone()
            lab_nombre = lab_info[0] if lab_info else codigo_lab
            
            cursor.execute("""
                INSERT INTO pacientes_laboratorios (paciente_id, codigo_lab)
                VALUES (%s, %s)
            """, (paciente_id, codigo_lab))
            
            lab_detalles.append(f"{codigo_lab} - {lab_nombre}")
        
        conn.commit()
        
        # Imprimir detalles de los laboratorios guardados
        print(f"Laboratorios guardados:")
        for detalle in lab_detalles:
            print(f"  - {detalle}")
        
        # Obtener el estado actual de Labs
        cursor.execute("SELECT labs FROM pacientes WHERE id = %s", (paciente_id,))
        resultado = cursor.fetchone()
        labs_estado = resultado[0] if resultado else ""
        
        conn.close()
        
        # Actualizar pendientes automáticamente según el estado de Labs
        print(f"Actualizando pendientes para Labs con estado: {labs_estado}")
        self.actualizar_pendientes_segun_labs(paciente_id, labs_estado)
        
        self.datos_actualizados.emit()
        print("✅ Laboratorios guardados correctamente")
        return True, "Laboratorios guardados correctamente"
    
    def obtener_imagenes_paciente(self, paciente_id):
        """Obtiene los exámenes de imagen asociados a un paciente"""
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.codigo_ix, i.nombre_ix, pi.estado 
            FROM pacientes_ixs pi
            JOIN imagenes i ON pi.codigo_ix = i.codigo_ix
            WHERE pi.paciente_id = %s
        """, (paciente_id,))
        imagenes = cursor.fetchall()
        conn.close()
        return imagenes
    
    def actualizar_columna_pendientes(self, paciente_id, pendientes_texto):
        """
        Actualiza la columna de pendientes para un paciente específico.
        
        Args:
            paciente_id: ID del paciente a actualizar
            pendientes_texto: Texto con los pendientes actualizados
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            
            # Obtener el nombre del paciente para el registro en consola
            cursor.execute("SELECT nombre, documento FROM pacientes WHERE id = %s", (paciente_id,))
            paciente_info = cursor.fetchone()
            nombre_paciente = paciente_info[0] if paciente_info else f"Paciente ID: {paciente_id}"
            documento_paciente = paciente_info[1] if paciente_info else "Desconocido"
            
            # Actualizar el campo de pendientes en la tabla principal
            cursor.execute("""
                UPDATE pacientes
                SET pendientes = %s
                WHERE id = %s
            """, (pendientes_texto, paciente_id))
            
            conn.commit()
            
            # Verificar si se realizaron cambios
            if cursor.rowcount > 0:
                print(f"\n[PENDIENTES ACTUALIZADOS] - {nombre_paciente} ({documento_paciente})")
                print(f"ID: {paciente_id}")
                print(f"Pendientes: {pendientes_texto}")
                # Emitir señal de datos actualizados para refrescar la interfaz
                self.datos_actualizados.emit()
                return True
            else:
                print(f"No se encontró paciente con ID: {paciente_id}")
                return False
                
        except Exception as e:
            print(f"Error al actualizar pendientes: {str(e)}")
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()
                
    def calcular_pendientes_auto(self, paciente_id):
        """
        Calcula automáticamente los pendientes basados en el estado de otros campos
        y los laboratorios e imágenes asignados al paciente.
        
        Args:
            paciente_id: ID del paciente
            
        Returns:
            str: Texto calculado de pendientes
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            
            # Obtener datos relevantes del paciente
            cursor.execute("""
                SELECT triage, ci, labs, ix, inter, rv, pendientes 
                FROM pacientes
                WHERE id = %s
            """, (paciente_id,))
            
            resultado = cursor.fetchone()
            
            if not resultado:
                return ""
            
            triage, ci, estado_labs, estado_ix, inter, rv, pendientes_actuales = resultado
            pendientes = []
            
            if pendientes_actuales:
                # Lista de pendientes automáticos específicos que serán regenerados
                pendientes_automaticos = [
                    "Valoración CI", "Abrir Interconsulta", "Respuesta Interconsulta",
                    "Realizar RV", "Realizar triage"
                ]
                
                # Filtrar pendientes eliminando todos los automáticos y los relacionados con labs/imágenes
                pendientes_personalizados = []
                for pendiente in pendientes_actuales.split(", "):
                    # Eliminar cualquier pendiente que contenga la palabra "Labs"
                    if not pendiente.startswith("Labs pendientes:") and "Labs" not in pendiente:
                        # Eliminar cualquier pendiente que contenga la palabra "IMG"
                        if not pendiente.startswith("IMG pendientes:") and "IMG" not in pendiente and "Resultados IMG" not in pendiente:
                            # Verificar si es un pendiente automático específico
                            es_automatico = any(p_auto in pendiente for p_auto in pendientes_automaticos)
                            
                            # Verificar si está relacionado con labs/imágenes
                            es_lab_img = pendiente.startswith("Labs pendientes:") or pendiente.startswith("IMG pendientes:")
                            
                            if not es_automatico and not es_lab_img:
                                cursor.execute("""
                                    SELECT COUNT(*) FROM (
                                        SELECT nombre_lab AS nombre FROM laboratorios
                                        WHERE nombre_lab = %s
                                        UNION
                                        SELECT nombre_ix AS nombre FROM imagenes
                                        WHERE nombre_ix = %s
                                    ) AS combined
                                """, (pendiente, pendiente))
                                
                                resultado_check = cursor.fetchone()
                                es_lab_img_item = resultado_check[0] > 0 if resultado_check else False
                                
                                # Solo agregar si no es un elemento de lab o imagen
                                if not es_lab_img_item:
                                    pendientes_personalizados.append(pendiente)
                
                # Actualizar la lista de pendientes con solo los personalizados no automáticos
                pendientes = pendientes_personalizados
                        
            # 1. Triage pendiente
            if triage in ["", "No realizado"] and "Realizar triage" not in pendientes:
                pendientes.append("Realizar triage")
            
            # 2. CI pendiente (solo si hay triage)
            if triage not in ["", "No realizado"] and ci == "No realizado" and "Valoración CI" not in pendientes:
                pendientes.append("Valoración CI")
            
            # 3. Si CI está realizado, verificar otros pendientes
            if ci == "Realizado":
                # 4. Verificar pendientes de Interconsulta
                if inter in ["No se ha abierto", "Abierta"]:
                    pendiente_texto = "Abrir Interconsulta" if inter == "No se ha abierto" else "Respuesta Interconsulta"
                    if pendiente_texto not in pendientes:
                        pendientes.append(pendiente_texto)
                
                # 5. Verificar pendientes de RV
                if rv == "No realizado" and "Realizar RV" not in pendientes:
                    pendientes.append("Realizar RV")
            
            # 7. Procesar laboratorios pendientes - Lista única y ordenada
            labs_pendientes_lista = []
            if ci == "Realizado" and estado_labs in ["No se ha realizado", "En espera de resultados"]:
                cursor.execute("""
                    SELECT DISTINCT l.nombre_lab 
                    FROM pacientes_laboratorios pl
                    JOIN laboratorios l ON pl.codigo_lab = l.codigo_lab
                    WHERE pl.paciente_id = %s
                    ORDER BY l.nombre_lab
                """, (paciente_id,))
                
                labs_pendientes = cursor.fetchall()
                
                if labs_pendientes:
                    # Extraer los nombres de los laboratorios y crear una lista única
                    labs_pendientes_lista = sorted(set(lab[0] for lab in labs_pendientes))
            
            # 8. Procesar imágenes pendientes - Lista única y ordenada
            img_pendientes_lista = []
            if ci == "Realizado" and estado_ix in ["No se ha realizado", "En espera de resultados"]:
                cursor.execute("""
                    SELECT DISTINCT i.nombre_ix 
                    FROM pacientes_ixs pi
                    JOIN imagenes i ON pi.codigo_ix = i.codigo_ix
                    WHERE pi.paciente_id = %s
                    ORDER BY i.nombre_ix
                """, (paciente_id,))
                
                img_pendientes = cursor.fetchall()
                
                if img_pendientes:
                    # Extraer los nombres de las imágenes y crear una lista única
                    img_pendientes_lista = sorted(set(img[0] for img in img_pendientes))
            
            # Añadir los pendientes de labs e imágenes si existen
            if labs_pendientes_lista:
                pendientes.append(f"Labs pendientes: {', '.join(labs_pendientes_lista)}")
            
            if img_pendientes_lista:
                pendientes.append(f"IMG pendientes: {', '.join(img_pendientes_lista)}")
            
            return ", ".join(pendientes)
            
        except Exception as e:
            print(f"Error al calcular pendientes automáticos: {str(e)}")
            return ""
        finally:
            if 'conn' in locals() and conn:
                conn.close()
    
    def guardar_imagenes_paciente(self, paciente_id, imagenes):
        """
        Guarda los exámenes de imagen asociados a un paciente y actualiza los pendientes.
        Valida que haya concordancia entre el estado de IX y las imágenes seleccionadas.
        
        Args:
            paciente_id: ID del paciente
            imagenes: Lista con códigos de imágenes a guardar
            
        Returns:
            tuple: (exito, mensaje) donde exito es un booleano y mensaje es un string
        """
        # Verificar primero si triage y CI están realizados
        conn = self.conectar()
        cursor = conn.cursor()
        
        # Obtener información del paciente para el registro en consola
        cursor.execute("SELECT nombre, documento, triage, ci, ix FROM pacientes WHERE id = %s", (paciente_id,))
        resultado = cursor.fetchone()
        
        if not resultado:
            conn.close()
            return False, "No se encontró el paciente"
        
        nombre_paciente = resultado[0]
        documento_paciente = resultado[1]
        triage, ci, estado_ix = resultado[2], resultado[3], resultado[4]
        
        # Imprimir información de seguimiento
        print(f"\n[GUARDANDO IMÁGENES] - {nombre_paciente} ({documento_paciente})")
        print(f"ID: {paciente_id}")
        print(f"Estado actual: Triage={triage}, CI={ci}, IMG={estado_ix}")
        print(f"Imágenes a guardar: {len(imagenes)}")
        
        # Validar que triage y CI estén realizados
        if triage not in ["1", "2", "3", "4", "5"] or ci != "Realizado":
            print(f"⚠️ Error: El triage y CI deben estar realizados antes de asociar imágenes")
            conn.close()
            return False, "El triage y CI deben estar realizados antes de asociar imágenes"
        
        # Validación de concordancia entre estado IX y imágenes seleccionadas
        estados_validos = ["No se ha realizado", "En espera de resultados", "Resultados completos"]
        
        # ✅ Si hay imágenes pero no se ha establecido un estado válido
        if imagenes and (not estado_ix or estado_ix not in estados_validos):
            print(f"⚠️ Error: Debe establecer un estado válido en IMG cuando selecciona imágenes")
            conn.close()
            return False, "Debe establecer un estado válido en IMG cuando selecciona imágenes"
            
        # ✅ Si hay un estado válido pero no hay imágenes seleccionadas
        if not imagenes and estado_ix in estados_validos:
            print(f"⚠️ Error: Ha seleccionado un estado para IMG pero no ha agregado ninguna imagen")
            conn.close()
            return False, "Ha seleccionado un estado para IMG pero no ha agregado ninguna imagen"
        
        # Si no hay imágenes y no hay estado, simplemente eliminar las asociaciones antiguas
        if not imagenes and (not estado_ix or estado_ix not in estados_validos):
            cursor.execute("DELETE FROM pacientes_ixs WHERE paciente_id = %s", (paciente_id,))
            # Actualizar el estado en la tabla de pacientes a vacío si tiene algún valor
            if estado_ix:
                cursor.execute("UPDATE pacientes SET ix = '' WHERE id = %s", (paciente_id,))
            conn.commit()
            conn.close()
            print("✅ No se asociaron imágenes (eliminadas asociaciones existentes)")
            return True, "No se asociaron imágenes"
        
        # Continuar con el procedimiento normal de inserción de imágenes
        cursor.execute("DELETE FROM pacientes_ixs WHERE paciente_id = %s", (paciente_id,))
        
        # Obtener detalles de las imágenes para mostrar en consola
        img_detalles = []
        
        # Insertar nuevas imágenes
        for codigo_ix in imagenes:
            # Obtener el nombre de la imagen para mostrar en consola
            cursor.execute("SELECT nombre_ix FROM imagenes WHERE codigo_ix = %s", (codigo_ix,))
            ix_info = cursor.fetchone()
            ix_nombre = ix_info[0] if ix_info else codigo_ix
            
            cursor.execute("""
                INSERT INTO pacientes_ixs (paciente_id, codigo_ix)
                VALUES (%s, %s)
            """, (paciente_id, codigo_ix))
            
            img_detalles.append(f"{codigo_ix} - {ix_nombre}")
        
        conn.commit()
        
        # Imprimir detalles de las imágenes guardadas
        print(f"Imágenes guardadas:")
        for detalle in img_detalles:
            print(f"  - {detalle}")
        
        # Obtener el estado actual de IX
        cursor.execute("SELECT ix FROM pacientes WHERE id = %s", (paciente_id,))
        resultado = cursor.fetchone()
        ix_estado = resultado[0] if resultado else ""
        
        conn.close()
        
        # Actualizar pendientes automáticamente según el estado de IX
        print(f"Actualizando pendientes para IMG con estado: {ix_estado}")
        self.actualizar_pendientes_segun_ix(paciente_id, ix_estado)
        
        self.datos_actualizados.emit()
        print("✅ Imágenes guardadas correctamente")
        return True, "Imágenes guardadas correctamente"
    
    def actualizar_pendientes_segun_labs(self, paciente_id, estado_labs):
        """
        Actualiza los pendientes basado en el estado de Labs
        
        Args:
            paciente_id: ID del paciente
            estado_labs: Estado actual del campo Labs
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            # Si Labs está completo, eliminar los pendientes relacionados con laboratorios
            if estado_labs == "Resultados completos":
                conn = self.conectar()
                cursor = conn.cursor()
                
                # Obtener pendientes actuales
                cursor.execute("SELECT pendientes FROM pacientes WHERE id = %s", (paciente_id,))
                resultado = cursor.fetchone()
                pendientes_actuales = resultado[0] if resultado and resultado[0] else ""
                
                # Filtrar pendientes para eliminar los relacionados con laboratorios
                pendientes_filtrados = []
                for pendiente in pendientes_actuales.split(", "):
                    # Eliminar cualquier pendiente que contenga la palabra "Labs"
                    if not pendiente.startswith("Labs pendientes:") and "Labs" not in pendiente:
                        pendientes_filtrados.append(pendiente)
                
                nuevos_pendientes = ", ".join(pendientes_filtrados)
                
                # Actualizar pendientes
                cursor.execute("UPDATE pacientes SET pendientes = %s WHERE id = %s", 
                              (nuevos_pendientes, paciente_id))
                conn.commit()
                conn.close()
                self.datos_actualizados.emit()
                return True
            else:
                # Si Labs no está completo, recalcular pendientes
                nuevos_pendientes = self.calcular_pendientes_auto(paciente_id)
                return self.actualizar_columna_pendientes(paciente_id, nuevos_pendientes)
        
        except Exception as e:
            print(f"Error al actualizar pendientes según estado de Labs: {str(e)}")
            return False
    
    def actualizar_pendientes_segun_ix(self, paciente_id, estado_ix):
        """
        Actualiza los pendientes basado en el estado de IX
        
        Args:
            paciente_id: ID del paciente
            estado_ix: Estado actual del campo IX
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            # Si IX está completo, eliminar los pendientes relacionados con imágenes
            if estado_ix == "Resultados completos":
                conn = self.conectar()
                cursor = conn.cursor()
                
                # Obtener pendientes actuales
                cursor.execute("SELECT pendientes FROM pacientes WHERE id = %s", (paciente_id,))
                resultado = cursor.fetchone()
                pendientes_actuales = resultado[0] if resultado and resultado[0] else ""
                
                # Filtrar pendientes para eliminar los relacionados con imágenes
                pendientes_filtrados = []
                for pendiente in pendientes_actuales.split(", "):
                    # Eliminar cualquier pendiente que contenga la palabra "IMG"
                    if not pendiente.startswith("IMG pendientes:") and "IMG" not in pendiente and "Resultados IMG" not in pendiente:
                        pendientes_filtrados.append(pendiente)
                
                nuevos_pendientes = ", ".join(pendientes_filtrados)
                
                # Actualizar pendientes
                cursor.execute("UPDATE pacientes SET pendientes = %s WHERE id = %s", 
                              (nuevos_pendientes, paciente_id))
                conn.commit()
                conn.close()
                self.datos_actualizados.emit()
                return True
            else:
                # Si IX no está completo, recalcular pendientes
                nuevos_pendientes = self.calcular_pendientes_auto(paciente_id)
                return self.actualizar_columna_pendientes(paciente_id, nuevos_pendientes)
        
        except Exception as e:
            print(f"Error al actualizar pendientes según estado de IX: {str(e)}")
            return False
    
    def actualizar_pendientes_segun_ci(self, paciente_id, estado_ci):
        """
        Actualiza los pendientes basado en el estado de CI
        
        Args:
            paciente_id: ID del paciente
            estado_ci: Estado actual del campo CI
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            # Si CI está Realizado, eliminar el pendiente relacionado con valoración de CI
            if estado_ci == "Realizado":
                conn = self.conectar()
                cursor = conn.cursor()
                
                # Obtener pendientes actuales
                cursor.execute("SELECT pendientes FROM pacientes WHERE id = %s", (paciente_id,))
                resultado = cursor.fetchone()
                pendientes_actuales = resultado[0] if resultado and resultado[0] else ""
                
                # Filtrar pendientes para eliminar los relacionados con CI
                pendientes_filtrados = []
                for pendiente in pendientes_actuales.split(", "):
                    if pendiente and pendiente != "Valoración CI":
                        pendientes_filtrados.append(pendiente)
                
                nuevos_pendientes = ", ".join(pendientes_filtrados)
                
                # Actualizar pendientes
                cursor.execute("UPDATE pacientes SET pendientes = %s WHERE id = %s", 
                              (nuevos_pendientes, paciente_id))
                conn.commit()
                conn.close()
                self.datos_actualizados.emit()
                return True
            else:
                # Si CI no está realizado, actualizar pendientes según corresponda
                nuevos_pendientes = self.calcular_pendientes_auto(paciente_id)
                return self.actualizar_columna_pendientes(paciente_id, nuevos_pendientes)
        
        except Exception as e:
            print(f"Error al actualizar pendientes según estado de CI: {str(e)}")
            return False
    
    def actualizar_pendientes_segun_triage(self, paciente_id, estado_triage):
        """
        Actualiza los pendientes basado en el estado del triage
        
        Args:
            paciente_id: ID del paciente
            estado_triage: Estado actual del campo triage
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            # Si triage está establecido (tiene un nivel), eliminar el pendiente relacionado
            if estado_triage in ["1", "2", "3", "4", "5"]:
                conn = self.conectar()
                cursor = conn.cursor()
                
                # Obtener pendientes actuales
                cursor.execute("SELECT pendientes FROM pacientes WHERE id = %s", (paciente_id,))
                resultado = cursor.fetchone()
                pendientes_actuales = resultado[0] if resultado and resultado[0] else ""
                
                # Filtrar pendientes para eliminar los relacionados con triage
                pendientes_filtrados = []
                for pendiente in pendientes_actuales.split(", "):
                    if pendiente and pendiente != "Realizar triage":
                        pendientes_filtrados.append(pendiente)
                
                nuevos_pendientes = ", ".join(pendientes_filtrados)
                
                # Actualizar pendientes
                cursor.execute("UPDATE pacientes SET pendientes = %s WHERE id = %s", 
                              (nuevos_pendientes, paciente_id))
                conn.commit()
                conn.close()
                self.datos_actualizados.emit()
                return True
            else:
                # Si triage no está establecido, añadir el pendiente correspondiente
                nuevos_pendientes = self.calcular_pendientes_auto(paciente_id)
                return self.actualizar_columna_pendientes(paciente_id, nuevos_pendientes)
        
        except Exception as e:
            print(f"Error al actualizar pendientes según estado de triage: {str(e)}")
            return False
    
    def actualizar_pendientes_segun_inter(self, paciente_id, estado_inter):
        """
        Actualiza los pendientes basado en el estado de la interconsulta
        
        Args:
            paciente_id: ID del paciente
            estado_inter: Estado actual del campo interconsulta
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            # Si la interconsulta está realizada, eliminar el pendiente relacionado
            if estado_inter == "Realizada":
                conn = self.conectar()
                cursor = conn.cursor()
                
                # Obtener pendientes actuales
                cursor.execute("SELECT pendientes FROM pacientes WHERE id = %s", (paciente_id,))
                resultado = cursor.fetchone()
                pendientes_actuales = resultado[0] if resultado and resultado[0] else ""
                
                # Filtrar pendientes para eliminar los relacionados con interconsulta
                pendientes_filtrados = []
                for pendiente in pendientes_actuales.split(", "):
                    if pendiente and pendiente != "Abrir Interconsulta" and pendiente != "Respuesta Interconsulta":
                        pendientes_filtrados.append(pendiente)
                
                nuevos_pendientes = ", ".join(pendientes_filtrados)
                
                # Actualizar pendientes
                cursor.execute("UPDATE pacientes SET pendientes = %s WHERE id = %s", 
                              (nuevos_pendientes, paciente_id))
                conn.commit()
                conn.close()
                self.datos_actualizados.emit()
                return True
            else:
                # Si la interconsulta no está realizada, recalcular pendientes
                nuevos_pendientes = self.calcular_pendientes_auto(paciente_id)
                return self.actualizar_columna_pendientes(paciente_id, nuevos_pendientes)
        
        except Exception as e:
            print(f"Error al actualizar pendientes según estado de interconsulta: {str(e)}")
            return False
    
    def actualizar_pendientes_segun_rv(self, paciente_id, estado_rv):
        """
        Actualiza los pendientes basado en el estado de RV
        
        Args:
            paciente_id: ID del paciente
            estado_rv: Estado actual del campo RV
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            # Si RV está realizado, eliminar el pendiente relacionado
            if estado_rv == "Realizado":
                conn = self.conectar()
                cursor = conn.cursor()
                
                # Obtener pendientes actuales
                cursor.execute("SELECT pendientes FROM pacientes WHERE id = %s", (paciente_id,))
                resultado = cursor.fetchone()
                pendientes_actuales = resultado[0] if resultado and resultado[0] else ""
                
                # Filtrar pendientes para eliminar los relacionados con RV
                pendientes_filtrados = []
                for pendiente in pendientes_actuales.split(", "):
                    if pendiente and pendiente != "Realizar RV":
                        pendientes_filtrados.append(pendiente)
                
                nuevos_pendientes = ", ".join(pendientes_filtrados)
                
                # Actualizar pendientes
                cursor.execute("UPDATE pacientes SET pendientes = %s WHERE id = %s", 
                              (nuevos_pendientes, paciente_id))
                conn.commit()
                conn.close()
                self.datos_actualizados.emit()
                return True
            else:
                # Si RV no está realizado, recalcular pendientes
                nuevos_pendientes = self.calcular_pendientes_auto(paciente_id)
                return self.actualizar_columna_pendientes(paciente_id, nuevos_pendientes)
        
        except Exception as e:
            print(f"Error al actualizar pendientes según estado de RV: {str(e)}")
            return False

    def obtener_nombre_usuario(self, username):
        """Obtiene el nombre completo del usuario desde la base de datos"""
        try:
            from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
            
            # Conectar a la base de datos
            conn = ModeloUsuarios.conectar_db()
            if not conn:
                return username  # Si no puede conectar, devuelve el username como fallback
                
            cursor = conn.cursor()
            
            # Consultar el nombre del usuario
            cursor.execute("""
                SELECT nombre_completo FROM usuarios 
                WHERE username = %s
            """, (username,))
            
            resultado = cursor.fetchone()
            conn.close()
            
            if resultado and resultado[0]:
                return resultado[0]
            else:
                return "Usuario del Sistema"  # Nombre genérico si no tiene nombre registrado
                
        except Exception as e:
            print(f"Error al obtener nombre de usuario: {str(e)}")
            return username 

    def actualizar_informacion_basica(self, datos, ubicacion, registro_original):
        """
        Actualiza información básica del paciente sin actualizar estados (que se manejarán con timestamps)
        
        Args:
            datos (dict): Diccionario de datos básicos del paciente
            ubicacion (str): Ubicación del paciente
            registro_original (tuple): Datos originales del paciente
            
        Returns:
            tuple: (exito, mensaje)
        """
        try:
            paciente_id = registro_original[13]  # ID en la posición 13
            
            conn = self.conectar()
            cursor = conn.cursor()
            
            # Actualiza solo nombre, documento, pendientes y ubicación
            query = """
                UPDATE pacientes
                SET nombre = %s, documento = %s, pendientes = %s, ubicacion = %s
                WHERE id = %s
            """
            
            params = (
                datos['nombre'],
                datos['documento'],
                datos['pendientes'],
                ubicacion,
                paciente_id
            )
            
            cursor.execute(query, params)
            conn.commit()
            
            return True, "Información básica actualizada correctamente"
            
        except Exception as e:
            print(f"Error al actualizar información básica: {str(e)}")
            return False, f"Error al actualizar información básica: {str(e)}"
        finally:
            if conn and hasattr(conn, 'close'):
                cursor.close()
                conn.close()

class ModeloTrazabilidad:
    """Modelo para gestionar la trazabilidad de acciones en el sistema"""
    
    @staticmethod
    def conectar():
        """Establece una conexión con la base de datos utilizando las credenciales actuales"""
        credenciales = ModeloAutenticacion.obtener_credenciales()
        return pymysql.connect(
            host=credenciales['equipo_trabajo'], 
            user=credenciales['usuario'], 
            password=credenciales['contrasena'], 
            database='sistema_visualizacion'
        )    
    
    @classmethod
    def registrar_accion(cls, usuario=None, rol=None, accion=None, paciente_afectado=None, detalles_cambio=None):
        """
        Registra una acción en la tabla de trazabilidad
        
        Args:
            usuario: Usuario que realizó la acción (si es None, se usa el usuario actual)
            rol: Rol del usuario (si es None, se infiere del usuario)
            accion: Descripción de la acción realizada
            paciente_afectado: Nombre del paciente afectado por la acción
            detalles_cambio: Detalles específicos del cambio realizado
            
        Returns:
            bool: True si se registró correctamente, False en caso contrario
        """
        try:
            # Si no se proporciona un usuario, utilizar el usuario autenticado actual
            if not usuario:
                credenciales = ModeloAutenticacion.obtener_credenciales()
                usuario = credenciales.get('usuario')
                
            # Si no hay usuario autenticado, no se puede registrar la acción
            if not usuario:
                print("No se pudo registrar trazabilidad: No hay usuario autenticado")
                return False
                
            # Obtener el rol del usuario si no se proporcionó
            if not rol:
                rol = cls.obtener_rol_usuario(usuario)
            # Conectar a la base de datos para buscar el ID del usuario
            conn = cls.conectar()
            cursor = conn.cursor()
            
            # Consultar el ID del usuario
            cursor.execute("SELECT id FROM usuarios WHERE username = %s", (usuario,))
            resultado = cursor.fetchone()
            usuario_id = resultado[0] if resultado else None
            
            # Registrar la acción en la tabla de trazabilidad
            sql = """
                INSERT INTO trazabilidad 
                (usuario, rol, accion, fecha_hora, paciente_afectado, detalles_cambio, usuario_id) 
                VALUES (%s, %s, %s, NOW(), %s, %s, %s)
            """
            cursor.execute(sql, (usuario, rol, accion, paciente_afectado, detalles_cambio, usuario_id))
            conn.commit()
            conn.close()
            
            print(f"✅ Acción registrada en trazabilidad: {usuario} ({rol}) - {accion}")
            return True            
        except Exception as e:
            print(f"Error al registrar acción en trazabilidad: {str(e)}")
            return False
    
    @classmethod
    def obtener_acciones(cls, search_terms=None, filtro_rol_usuario=None, limite=200, pagina=1):
        """
        Obtiene las acciones de trazabilidad filtradas según los parámetros
        
        Args:
            search_terms: Lista de términos de búsqueda (se aplican con AND)
            filtro_rol_usuario: Filtrar por rol de usuario (Administrador, Médico, etc.)
            limite: Límite de resultados a retornar
            pagina: Número de página para paginación
            
        Returns:
            list: Lista de acciones que cumplen los criterios
        """
        try:
            conn = cls.conectar()
            cursor = conn.cursor()
            
            # Construir la consulta base
            sql = """
                SELECT t.usuario, t.rol, t.accion, t.fecha_hora, 
                       t.paciente_afectado, t.detalles_cambio, t.usuario_id, u.nombre_completo
                FROM trazabilidad t
                LEFT JOIN usuarios u ON t.usuario = u.username
                WHERE 1=1
            """
            
            params = []
            
            # Agregar condiciones de búsqueda por términos
            if search_terms and len(search_terms) > 0:
                # Crear condiciones para cada término de búsqueda
                term_conditions = []
                
                for term in search_terms:
                    term_condition = """
                        (LOWER(t.usuario) LIKE %s 
                        OR LOWER(u.nombre_completo) LIKE %s
                        OR LOWER(t.paciente_afectado) LIKE %s
                        OR LOWER(t.detalles_cambio) LIKE %s)
                    """
                    term_conditions.append(term_condition)
                    texto_busqueda = f"%{term.lower()}%"
                    params.extend([texto_busqueda, texto_busqueda, texto_busqueda, texto_busqueda])
                
                # Combinar todas las condiciones con AND para que se cumplan todos los términos
                if term_conditions:
                    sql += " AND " + " AND ".join(term_conditions)
            
            # Agregar filtro por rol si está presente
            if filtro_rol_usuario:
                sql += """ 
                    AND t.usuario IN (
                        SELECT username FROM usuarios 
                        WHERE CASE 
                            WHEN %s = 'Administrador' THEN rol_admin = 1
                            WHEN %s = 'Médico' THEN rol_medico = 1
                            ELSE 0 END
                    )
                """
                params.extend([filtro_rol_usuario, filtro_rol_usuario])
            
            # Calcular offset para paginación
            offset = (pagina - 1) * limite
            
            # Ordenar por fecha descendente y establecer límite con paginación
            sql += " ORDER BY t.fecha_hora DESC LIMIT %s OFFSET %s"
            params.extend([limite, offset])
            
            # Ejecutar consulta
            cursor.execute(sql, params)
            resultados = cursor.fetchall()
            
            conn.close()
            
            # Convertir resultados a lista de listas para mantener consistencia
            resultados_lista = [list(fila) for fila in resultados]
            
            return resultados_lista
            
        except Exception as e:
            print(f"Error al obtener acciones de trazabilidad: {str(e)}")
            return []

    @classmethod
    def obtener_rol_usuario(cls, username):
        """Obtiene el rol de un usuario desde la base de datos"""
        try:
            from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
            return ModeloUsuarios.obtener_rol_usuario(username)
        except Exception as e:
            print(f"Error al obtener rol del usuario: {str(e)}")
            return 'Sin rol'
            
    @classmethod
    def calcular_y_almacenar_metricas(cls, paciente_id):
        """
        Calcula y almacena métricas para un paciente basado en sus timestamps.
        Si ya existen métricas para este paciente, las actualiza en lugar de crear nuevas filas.
        
        Args:
            paciente_id: ID del paciente para calcular métricas
            
        Returns:
            bool: True si se calcularon y guardaron correctamente, False en caso contrario
        """
        conn = None
        try:
            conn = cls.conectar()
            cursor = conn.cursor()
            
            # Obtener todos los timestamps relevantes para el paciente
            cursor.execute("""
                SELECT 
                    ingreso, triage_timestamp, 
                    ci_no_realizado_timestamp, ci_realizado_timestamp,
                    labs_no_realizado_timestamp, labs_solicitados_timestamp, labs_completos_timestamp,
                    ix_no_realizado_timestamp, ix_solicitados_timestamp, ix_completos_timestamp,
                    inter_no_abierta_timestamp, inter_abierta_timestamp, inter_realizada_timestamp,
                    rv_no_realizado_timestamp, rv_realizado_timestamp,
                    alta_timestamp, triage, ubicacion
                FROM pacientes
                WHERE id = %s
            """, (paciente_id,))
            
            result = cursor.fetchone()
            if not result:
                print(f"No se encontró el paciente {paciente_id}")
                return False
                
            # Desempaquetar resultados
            (ingreso, triage_timestamp, 
             ci_no_realizado, ci_realizado,
             labs_no_realizado, labs_solicitados, labs_completos,
             ix_no_realizado, ix_solicitados, ix_completos,
             inter_no_abierta, inter_abierta, inter_realizada,
             rv_no_realizado, rv_realizado,
             alta_timestamp, triage, ubicacion) = result
            
            # Inicializar diccionario para almacenar métricas
            metricas = {
                'paciente_id': paciente_id,
                'area': ubicacion
            }
            
            # Extraer clase de triage (dígito 1-5)
            if triage in ["1", "2", "3", "4", "5"]:
                metricas['clase_triage'] = triage
            
            # Tiempo de triage
            if ingreso and triage_timestamp:
                tiempo_triage = int((triage_timestamp - ingreso).total_seconds() / 60)
                metricas['tiempo_triage'] = tiempo_triage
            
            # Tiempo de CI - FIX: Calcular si existe el timestamp de realizado, independientemente de los otros pasos
            if ci_no_realizado and ci_realizado:
                tiempo_ci = int((ci_realizado - ci_no_realizado).total_seconds() / 60)
                metricas['tiempo_ci'] = tiempo_ci
            
            # Tiempos de Labs - FIX: Calcular cada parte por separado si existen los timestamps necesarios
            if labs_no_realizado and labs_solicitados:
                tiempo_labs_solicitud = int((labs_solicitados - labs_no_realizado).total_seconds() / 60)
                metricas['tiempo_labs_solicitud'] = tiempo_labs_solicitud
            
            if labs_solicitados and labs_completos:
                tiempo_labs_resultados = int((labs_completos - labs_solicitados).total_seconds() / 60)
                metricas['tiempo_labs_resultados'] = tiempo_labs_resultados
            
            if labs_no_realizado and labs_completos:
                tiempo_labs_total = int((labs_completos - labs_no_realizado).total_seconds() / 60)
                metricas['tiempo_labs_total'] = tiempo_labs_total
            
            # Tiempos de IX - FIX: Calcular cada parte por separado si existen los timestamps necesarios
            if ix_no_realizado and ix_solicitados:
                tiempo_ix_solicitud = int((ix_solicitados - ix_no_realizado).total_seconds() / 60)
                metricas['tiempo_ix_solicitud'] = tiempo_ix_solicitud
            
            if ix_solicitados and ix_completos:
                tiempo_ix_resultados = int((ix_completos - ix_solicitados).total_seconds() / 60)
                metricas['tiempo_ix_resultados'] = tiempo_ix_resultados
            
            if ix_no_realizado and ix_completos:
                tiempo_ix_total = int((ix_completos - ix_no_realizado).total_seconds() / 60)
                metricas['tiempo_ix_total'] = tiempo_ix_total
            
            # Tiempos de Interconsulta - FIX: Calcular cada parte por separado si existen los timestamps necesarios
            if inter_no_abierta and inter_abierta:
                tiempo_inter_apertura = int((inter_abierta - inter_no_abierta).total_seconds() / 60)
                metricas['tiempo_inter_apertura'] = tiempo_inter_apertura
            
            if inter_abierta and inter_realizada:
                tiempo_inter_realizacion = int((inter_realizada - inter_abierta).total_seconds() / 60)
                metricas['tiempo_inter_realizacion'] = tiempo_inter_realizacion
            
            if inter_no_abierta and inter_realizada:
                tiempo_inter_total = int((inter_realizada - inter_no_abierta).total_seconds() / 60)
                metricas['tiempo_inter_total'] = tiempo_inter_total
            
            # Tiempo de RV - FIX: Calcular si existen los timestamps necesarios
            if rv_no_realizado and rv_realizado:
                tiempo_rv = int((rv_realizado - rv_no_realizado).total_seconds() / 60)
                metricas['tiempo_rv'] = tiempo_rv
            
            ultimo_timestamp = None
            if alta_timestamp:
                ultimo_timestamp = alta_timestamp
            else:
                # Intentar usar el último timestamp disponible de cualquier proceso finalizado
                timestamps_finales = [
                    triage_timestamp, ci_no_realizado, ci_realizado, labs_no_realizado, labs_solicitados, labs_completos, 
                    ix_no_realizado, ix_solicitados, ix_completos, inter_no_abierta, inter_abierta, inter_realizada, rv_no_realizado, rv_realizado
                ]
                timestamps_validos = [ts for ts in timestamps_finales if ts is not None]
                if timestamps_validos:
                    ultimo_timestamp = max(timestamps_validos)
            
            # Ahora calcular el tiempo total con el último timestamp si está disponible
            if ingreso and ultimo_timestamp:
                tiempo_total_atencion = int((ultimo_timestamp - ingreso).total_seconds() / 60)
                metricas['tiempo_total_atencion'] = tiempo_total_atencion
            
            # Verificar si ya existen métricas para este paciente
            cursor.execute("SELECT id FROM metricas_pacientes WHERE paciente_id = %s", (paciente_id,))
            metrica_existente = cursor.fetchone()
            
            if metricas:
                if metrica_existente:
                    # Si existe, actualizar el registro existente
                    update_fields = []
                    update_values = []
                    
                    for campo, valor in metricas.items():
                        if campo != 'paciente_id':  # No actualizar el paciente_id
                            update_fields.append(f"{campo} = %s")
                            update_values.append(valor)
                    
                    # Añadir la fecha de actualización
                    update_fields.append("fecha_calculo = NOW()")
                    
                    # Añadir el ID al final para la cláusula WHERE
                    update_values.append(paciente_id)
                    
                    # Construir la consulta de actualización
                    update_query = f"""
                        UPDATE metricas_pacientes 
                        SET {", ".join(update_fields)}
                        WHERE paciente_id = %s
                    """
                    
                    cursor.execute(update_query, update_values)
                else:
                    # Si no existe, insertar un nuevo registro
                    campos = []
                    valores = []
                    placeholders = []
                    
                    for campo, valor in metricas.items():
                        campos.append(campo)
                        valores.append(valor)
                        placeholders.append("%s")
                    
                    # Construir la consulta de inserción
                    insert_query = f"""
                        INSERT INTO metricas_pacientes 
                        ({", ".join(campos)}, fecha_calculo) 
                        VALUES ({", ".join(placeholders)}, NOW())
                    """
                    
                    cursor.execute(insert_query, valores)
                
                conn.commit()
                print(f"Métricas actualizadas/guardadas para paciente {paciente_id}")
                return True
            else:
                print(f"No hay métricas para guardar para paciente {paciente_id}")
                return False
                
        except Exception as e:
            print(f"Error al calcular o guardar métricas para paciente {paciente_id}: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
